import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

import aio_pika
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from core.rag_service import delete_knowledge_file_vectors
from core.upload_validation import resolve_upload_path, validate_upload_metadata
from dependencies import get_session
from repository.knowledge_repo import KnowledgeRepository
from repository.security_repo import SecurityRepository
from repository.task_repo import TaskRepository
from schemas.knowledge_schemas import (
    AdminKnowledgeFileOut,
    KnowledgeFileOut,
    KnowledgeUploadOut,
)


auth_handler = AuthHandler()
router = APIRouter(prefix="/knowledge", tags=["知识库"])
admin_router = APIRouter(prefix="/admin/knowledge/files", tags=["运营后台·知识库"])
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
load_dotenv()
RABBITMQ_URL = os.getenv("RABBITMQ_URL")
QUEUE_NAME = "rag_document_queue"


async def send_to_queue(message_dict: dict):
    if not RABBITMQ_URL:
        raise RuntimeError("没有读取到 RABBITMQ_URL，请检查 .env 文件")
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message_dict).encode("utf-8"),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue.name,
        )


def task_payload(item) -> dict:
    return {
        "file_id": item.id,
        "user_id": item.user_id,
        "file_path": item.storage_path,
        "version": item.processing_version,
    }


def task_for(item, background_task) -> dict:
    return {"task_id": background_task.id, **task_payload(item)}


def safe_storage_path(raw_path: str) -> Path:
    return resolve_upload_path(raw_path, UPLOAD_DIR)


async def enqueue_or_fail(item, background_task, session: AsyncSession) -> None:
    try:
        await send_to_queue(task_for(item, background_task))
    except Exception as exc:
        await KnowledgeRepository(session).mark_enqueue_failed(item.id, f"任务入队失败：{exc}")
        await TaskRepository(session).mark_enqueue_failed(
            background_task.id, f"任务入队失败：{exc}"
        )
        raise HTTPException(status_code=503, detail="任务队列暂不可用，文件已保留，可稍后重新处理") from exc


@router.post("/upload", response_model=KnowledgeUploadOut)
async def upload_file(
    file: UploadFile = File(...),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    try:
        original_name, extension, content_type = validate_upload_metadata(
            file.filename, file.content_type
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    content = await file.read(MAX_UPLOAD_SIZE + 1)
    if not content:
        raise HTTPException(status_code=400, detail="上传文件不能为空")
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="文件不能超过 10MB")
    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="PDF 文件内容格式错误")
    if extension == ".txt":
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="TXT 文件必须使用 UTF-8 编码") from exc

    file_path = (UPLOAD_DIR / f"{user_id}_{uuid4().hex}{extension}").resolve()
    if UPLOAD_DIR.resolve() not in file_path.parents:
        raise HTTPException(status_code=400, detail="文件路径无效")
    await run_in_threadpool(file_path.write_bytes, content)
    try:
        async with session.begin():
            item = await KnowledgeRepository(session).create_in_transaction(
                user_id=user_id,
                original_name=original_name,
                storage_path=str(file_path),
                extension=extension,
                mime_type=content_type,
                size_bytes=len(content),
                checksum=hashlib.sha256(content).hexdigest(),
            )
            background_task = await TaskRepository(session).create_in_transaction(
                user_id=user_id,
                task_type="knowledge.process",
                target_type="knowledge_file",
                target_id=str(item.id),
                payload=task_payload(item),
            )
    except Exception:
        await run_in_threadpool(file_path.unlink, True)
        raise
    await enqueue_or_fail(item, background_task, session)
    return {
        "result": "success",
        "message": "文件已上传并进入处理队列",
        "file": item,
        "task_id": background_task.id,
    }


@router.get("/files", response_model=list[KnowledgeFileOut])
async def list_files(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await KnowledgeRepository(session).list_for_user(user_id)


@router.get("/files/{file_id}", response_model=KnowledgeFileOut)
async def file_detail(
    file_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    item = await KnowledgeRepository(session).get_for_user(file_id, user_id)
    if item is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    return item


async def retry_item(file_id: int, session: AsyncSession, user_id: int | None):
    try:
        item = await KnowledgeRepository(session).retry(file_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    if not safe_storage_path(item.storage_path).exists():
        await KnowledgeRepository(session).mark_enqueue_failed(item.id, "源文件不存在")
        raise HTTPException(status_code=409, detail="源文件不存在，无法重新处理")
    try:
        background_task = await TaskRepository(session).create(
            user_id=item.user_id,
            task_type="knowledge.process",
            target_type="knowledge_file",
            target_id=str(item.id),
            payload=task_payload(item),
        )
    except Exception as exc:
        await KnowledgeRepository(session).mark_enqueue_failed(
            item.id, f"任务记录创建失败：{exc}"
        )
        raise
    await enqueue_or_fail(item, background_task, session)
    return item


async def delete_item(file_id: int, session: AsyncSession, user_id: int | None):
    item = await KnowledgeRepository(session).mark_deleted(file_id, user_id)
    if item is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    await TaskRepository(session).cancel_queued_for_target(
        "knowledge_file", str(item.id)
    )
    try:
        await run_in_threadpool(delete_knowledge_file_vectors, item.user_id, item.id)
        await run_in_threadpool(safe_storage_path(item.storage_path).unlink, True)
    except Exception as exc:
        await KnowledgeRepository(session).fail_delete(
            item.id, item.processing_version, str(exc)
        )
        raise HTTPException(status_code=503, detail="文件清理失败，请稍后重试删除") from exc
    await KnowledgeRepository(session).finish_delete(item.id, item.processing_version)
    return item


@router.post("/files/{file_id}/reprocess", response_model=KnowledgeFileOut)
async def reprocess_file(
    file_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await retry_item(file_id, session, user_id)


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    await delete_item(file_id, session, user_id)
    return {"message": "知识库文件已删除"}


@admin_router.get("", response_model=list[AdminKnowledgeFileOut])
async def admin_list_files(
    status: str | None = Query(None),
    admin_id: int = Depends(auth_handler.require_permissions("knowledge.manage")),
    session: AsyncSession = Depends(get_session),
):
    rows = await KnowledgeRepository(session).list_all(status)
    return [{**KnowledgeFileOut.model_validate(item).model_dump(), "user_id": user.id,
             "user_email": user.email, "username": user.username} for item, user in rows]


def request_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@admin_router.post("/{file_id}/reprocess", response_model=KnowledgeFileOut)
async def admin_reprocess_file(
    file_id: int,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("knowledge.manage")),
    session: AsyncSession = Depends(get_session),
):
    item = await retry_item(file_id, session, None)
    await SecurityRepository(session).audit(
        admin_user_id=admin_id,
        action="knowledge.reprocess",
        target_type="knowledge_file",
        target_id=str(file_id),
        detail="{}",
        ip_address=request_ip(request),
    )
    return item


@admin_router.delete("/{file_id}")
async def admin_delete_file(
    file_id: int,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("knowledge.manage")),
    session: AsyncSession = Depends(get_session),
):
    await delete_item(file_id, session, None)
    await SecurityRepository(session).audit(
        admin_user_id=admin_id,
        action="knowledge.delete",
        target_type="knowledge_file",
        target_id=str(file_id),
        detail="{}",
        ip_address=request_ip(request),
    )
    return {"message": "知识库文件已删除"}
