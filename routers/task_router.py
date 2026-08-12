import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from dependencies import get_session
from repository.knowledge_repo import KnowledgeRepository
from repository.security_repo import SecurityRepository
from repository.task_repo import TaskRepository
from routers.rag_router import send_to_queue
from schemas.task_schemas import AdminAsyncTaskOut, AsyncTaskOut


auth_handler = AuthHandler()
router = APIRouter(prefix="/tasks", tags=["异步任务"])
admin_router = APIRouter(prefix="/admin/tasks", tags=["运营后台·异步任务"])


def queue_message(task) -> dict:
    payload = json.loads(task.payload)
    return {"task_id": task.id, **payload}


async def prepare_target_for_retry(task, session: AsyncSession) -> None:
    payload = json.loads(task.payload)
    if task.task_type == "knowledge.process":
        ready = await KnowledgeRepository(session).prepare_task_retry(
            int(payload["file_id"]), int(payload["version"])
        )
        if not ready:
            raise HTTPException(status_code=409, detail="任务关联文件当前无法重试")


async def retry_task(task_id: str, session: AsyncSession, user_id: int | None):
    try:
        task = await TaskRepository(session).manual_retry(task_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    try:
        await prepare_target_for_retry(task, session)
        await send_to_queue(queue_message(task))
    except HTTPException:
        await TaskRepository(session).mark_enqueue_failed(task.id, "关联业务对象无法重试")
        raise
    except Exception as exc:
        await TaskRepository(session).mark_enqueue_failed(task.id, f"任务入队失败：{exc}")
        raise HTTPException(status_code=503, detail="任务队列暂不可用，请稍后重试") from exc
    return task


@router.get("", response_model=list[AsyncTaskOut])
async def list_my_tasks(
    status: str | None = Query(None),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await TaskRepository(session).list_for_user(user_id, status)


@router.get("/{task_id}", response_model=AsyncTaskOut)
async def task_detail(
    task_id: str,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    task = await TaskRepository(session).get_for_user(task_id, user_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.post("/{task_id}/retry", response_model=AsyncTaskOut)
async def retry_my_task(
    task_id: str,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await retry_task(task_id, session, user_id)


@admin_router.get("", response_model=list[AdminAsyncTaskOut])
async def admin_list_tasks(
    status: str | None = Query(None),
    task_type: str | None = Query(None),
    admin_id: int = Depends(auth_handler.require_permissions("tasks.manage")),
    session: AsyncSession = Depends(get_session),
):
    rows = await TaskRepository(session).list_all(status, task_type)
    return [{
        **AsyncTaskOut.model_validate(task).model_dump(),
        "user_id": user.id,
        "user_email": user.email,
        "username": user.username,
    } for task, user in rows]


def request_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@admin_router.post("/{task_id}/retry", response_model=AsyncTaskOut)
async def admin_retry_task(
    task_id: str,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("tasks.manage")),
    session: AsyncSession = Depends(get_session),
):
    task = await retry_task(task_id, session, None)
    await SecurityRepository(session).audit(
        admin_user_id=admin_id,
        action="task.retry",
        target_type="async_task",
        target_id=task_id,
        detail="{}",
        ip_address=request_ip(request),
    )
    return task


@admin_router.post("/{task_id}/cancel", response_model=AsyncTaskOut)
async def admin_cancel_task(
    task_id: str,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("tasks.manage")),
    session: AsyncSession = Depends(get_session),
):
    try:
        task = await TaskRepository(session).cancel(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    payload = json.loads(task.payload)
    if task.task_type == "knowledge.process":
        await KnowledgeRepository(session).cancel_queued(
            int(payload["file_id"]), int(payload["version"]), "关联任务已被管理员取消"
        )
    await SecurityRepository(session).audit(
        admin_user_id=admin_id,
        action="task.cancel",
        target_type="async_task",
        target_id=task_id,
        detail="{}",
        ip_address=request_ip(request),
    )
    return task
