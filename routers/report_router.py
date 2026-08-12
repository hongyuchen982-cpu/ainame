import asyncio
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from core.distributed_lock import OperationBusyError, distributed_operation_lock
from core.redistools import get_redis
from core.report_service import generate_naming_report_pdf
from dependencies import get_session
from repository.brand_asset_repo import BrandAssetRepository
from repository.project_repo import NamingProjectRepository
from repository.report_repo import NamingReportRepository
from repository.validation_repo import NameValidationRepository
from schemas.report_schemas import (
    AdminNamingReportOut,
    NamingReportCreateIn,
    NamingReportOut,
)


auth_handler = AuthHandler()
router = APIRouter(prefix="/reports", tags=["PDF 命名报告"])
admin_router = APIRouter(prefix="/admin/reports", tags=["运营后台·PDF 报告"])
REPORT_DIR = Path(__file__).resolve().parents[1] / "output" / "pdf"


def _report_out(item) -> dict:
    return {
        "id": item.id,
        "project_id": item.project_id,
        "selected_name_id": item.selected_name_id,
        "validation_id": item.validation_id,
        "brand_asset_id": item.brand_asset_id,
        "client_request_id": item.client_request_id,
        "title": item.title,
        "name": item.name,
        "file_size": item.file_size,
        "page_count": item.page_count,
        "sha256": item.sha256,
        "download_url": f"/reports/{item.id}/download",
        "created_at": item.created_at,
    }


def _validation_snapshot(item) -> dict | None:
    if item is None:
        return None
    return {
        "id": item.id,
        "risk_score": item.risk_score,
        "risk_level": item.risk_level,
        "coverage": item.coverage,
        "risk_summary": item.risk_summary,
        "domains": item.domains,
        "trademark": item.trademark,
        "company": item.company,
        "social": item.social,
        "created_at": item.created_at.isoformat(),
    }


def _asset_snapshot(item) -> dict | None:
    if item is None:
        return None
    return {
        "id": item.id,
        "positioning": item.positioning,
        "slogans": item.slogans,
        "logo_concepts": item.logo_concepts,
        "visual_guidelines": item.visual_guidelines,
        "domain_matrix": item.domain_matrix,
        "risk_notes": item.risk_notes,
        "created_at": item.created_at.isoformat(),
    }


@router.post("", response_model=NamingReportOut)
async def create_report(
    data: NamingReportCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    repository = NamingReportRepository(session)
    existing = await repository.get_by_request(data.client_request_id, user_id)
    if existing is not None:
        return _report_out(existing)
    try:
        async with distributed_operation_lock(
            redis, f"lock:report:request:{user_id}:{data.client_request_id}"
        ):
            async with distributed_operation_lock(
                redis, f"lock:report:project:{data.project_id}"
            ):
                item = await _create_report_locked(data, user_id, session, repository)
                return _report_out(item)
    except OperationBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


async def _create_report_locked(data, user_id, session, repository):
    existing = await repository.get_by_request(data.client_request_id, user_id)
    if existing is not None:
        return existing
    project, rounds, selected = await NamingProjectRepository(session).detail_parts(
        data.project_id, user_id
    )
    if project is None:
        raise HTTPException(status_code=404, detail="命名项目不存在")
    if selected is None:
        raise HTTPException(status_code=400, detail="请先为项目选定最终名称")

    validation_repo = NameValidationRepository(session)
    if data.validation_id is not None:
        validation = await validation_repo.get_for_user(data.validation_id, user_id)
        if validation is None:
            raise HTTPException(status_code=404, detail="名称校验记录不存在")
        if validation.selected_name_id != selected.id:
            raise HTTPException(
                status_code=400, detail="名称校验记录与项目最终名称不匹配"
            )
    else:
        validation = await validation_repo.latest_for_selection(selected.id, user_id)

    asset_repo = BrandAssetRepository(session)
    if data.brand_asset_id is not None:
        asset = await asset_repo.get_for_user(data.brand_asset_id, user_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="品牌资产不存在")
        if asset.selected_name_id != selected.id:
            raise HTTPException(status_code=400, detail="品牌资产与项目最终名称不匹配")
    else:
        asset = await asset_repo.latest_for_project(project.id, user_id)

    reference = f"REPORT-{datetime.now():%Y%m%d}-{uuid4().hex[:8].upper()}"
    snapshot = {
        "report_reference": reference,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project": {
            "id": project.id,
            "title": project.title,
            "category": project.category,
            "status": project.status,
            "conditions": project.conditions,
            "created_at": project.created_at.isoformat(),
        },
        "final_selection": {
            "id": selected.id,
            "name": selected.name,
            "reference": selected.reference,
            "moral": selected.moral,
            "logo_url": selected.logo_url,
        },
        "rounds": [
            {
                "round_no": naming_round.round_no,
                "feedback": naming_round.feedback,
                "created_at": naming_round.created_at.isoformat(),
                "candidates": [
                    {
                        "name": candidate.name,
                        "reference": candidate.reference,
                        "moral": candidate.moral,
                        "domain": candidate.domain,
                        "domain_status": candidate.domain_status,
                    }
                    for candidate in candidates
                ],
            }
            for naming_round, candidates in rounds
        ],
        "validation": _validation_snapshot(validation),
        "brand_asset": _asset_snapshot(asset),
    }
    filename = f"naming-report-{uuid4().hex}.pdf"
    try:
        metadata = await asyncio.to_thread(
            generate_naming_report_pdf, snapshot, REPORT_DIR, filename
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="PDF 报告生成失败，请稍后重试"
        ) from exc
    try:
        return await repository.create(
            user_id=user_id,
            project_id=project.id,
            selected_name_id=selected.id,
            validation_id=validation.id if validation else None,
            brand_asset_id=asset.id if asset else None,
            client_request_id=data.client_request_id,
            title=f"{project.title} - 命名价值报告",
            name=selected.name,
            filename=metadata["filename"],
            file_size=metadata["file_size"],
            page_count=metadata["page_count"],
            sha256=metadata["sha256"],
            snapshot=snapshot,
        )
    except Exception:
        (REPORT_DIR / filename).unlink(missing_ok=True)
        raise


@router.get("", response_model=list[NamingReportOut])
async def list_reports(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return [
        _report_out(item)
        for item in await NamingReportRepository(session).list_for_user(user_id)
    ]


@router.get("/{report_id}", response_model=NamingReportOut)
async def report_detail(
    report_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    item = await NamingReportRepository(session).get_for_user(report_id, user_id)
    if item is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    return _report_out(item)


def _download_response(item, admin: bool = False):
    path = REPORT_DIR / Path(item.filename).name
    if not path.is_file():
        raise HTTPException(status_code=410, detail="报告文件已丢失，请重新生成")
    prefix = "/admin" if admin else ""
    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=f"naming-report-{item.id}.pdf",
        headers={
            "X-Report-SHA256": item.sha256,
            "X-Report-URL": f"{prefix}/reports/{item.id}/download",
        },
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    item = await NamingReportRepository(session).get_for_user(report_id, user_id)
    if item is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    return _download_response(item)


@admin_router.get("", response_model=list[AdminNamingReportOut])
async def admin_list_reports(
    admin_id: int = Depends(auth_handler.require_permissions("reports.manage")),
    session: AsyncSession = Depends(get_session),
):
    rows = await NamingReportRepository(session).list_all()
    return [
        {
            **_report_out(item),
            "user_id": user.id,
            "user_email": user.email,
            "username": user.username,
        }
        for item, user in rows
    ]


@admin_router.get("/{report_id}/download")
async def admin_download_report(
    report_id: int,
    admin_id: int = Depends(auth_handler.require_permissions("reports.manage")),
    session: AsyncSession = Depends(get_session),
):
    item = await NamingReportRepository(session).get_any(report_id)
    if item is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    return _download_response(item, admin=True)
