import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from dependencies import get_session
from repository.community_repo import CommunityRepository
from repository.security_repo import SecurityRepository
from routers.admin_router import request_ip
from schemas.community_schemas import (
    CommunityCommentIn, CommunityFeatureIn, CommunityModerateIn,
    CommunityPollCreateIn, CommunityPollOut, CommunityReportIn,
    CommunityReportOut, CommunityVoteIn,
)


router = APIRouter(prefix="/community", tags=["社区众包"])
admin_router = APIRouter(prefix="/admin/community", tags=["运营后台·社区"])
auth_handler = AuthHandler()


def report_out(item, reporter):
    return {"id": item.id, "reporter": reporter.username, "target_type": item.target_type, "target_id": item.target_id, "reason": item.reason, "status": item.status, "resolution": item.resolution, "created_at": item.created_at, "resolved_at": item.resolved_at}


@router.post("/polls", response_model=CommunityPollOut)
async def create_poll(data: CommunityPollCreateIn, user_id: int = Depends(auth_handler.auth_access_dependency), session: AsyncSession = Depends(get_session)):
    repo = CommunityRepository(session)
    try: poll = await repo.create_poll(user_id, **data.model_dump())
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    return await repo.poll(poll.id, user_id)


@router.get("/polls", response_model=list[CommunityPollOut])
async def polls(featured: bool = False, mine: bool = False, user_id: int = Depends(auth_handler.auth_access_dependency), session: AsyncSession = Depends(get_session)):
    return await CommunityRepository(session).list_polls(user_id, featured=featured, mine=mine)


@router.get("/polls/{poll_id}", response_model=CommunityPollOut)
async def poll_detail(poll_id: int, user_id: int = Depends(auth_handler.auth_access_dependency), session: AsyncSession = Depends(get_session)):
    item = await CommunityRepository(session).poll(poll_id, user_id)
    if not item: raise HTTPException(404, "社区投票不存在")
    return item


@router.post("/polls/{poll_id}/vote", response_model=CommunityPollOut)
async def vote(poll_id: int, data: CommunityVoteIn, user_id: int = Depends(auth_handler.auth_access_dependency), session: AsyncSession = Depends(get_session)):
    repo = CommunityRepository(session)
    try: await repo.vote(poll_id, data.candidate_id, user_id)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    return await repo.poll(poll_id, user_id)


@router.post("/polls/{poll_id}/comments", response_model=CommunityPollOut)
async def comment(poll_id: int, data: CommunityCommentIn, user_id: int = Depends(auth_handler.auth_access_dependency), session: AsyncSession = Depends(get_session)):
    repo = CommunityRepository(session)
    try: await repo.add_comment(poll_id, user_id, data.content)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    return await repo.poll(poll_id, user_id)


@router.post("/polls/{poll_id}/close", response_model=CommunityPollOut)
async def close_poll(poll_id: int, user_id: int = Depends(auth_handler.auth_access_dependency), session: AsyncSession = Depends(get_session)):
    repo = CommunityRepository(session)
    try: await repo.close_poll(poll_id, user_id)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    return await repo.poll(poll_id, user_id)


@router.post("/reports", response_model=CommunityReportOut)
async def report(data: CommunityReportIn, user_id: int = Depends(auth_handler.auth_access_dependency), session: AsyncSession = Depends(get_session)):
    repo = CommunityRepository(session)
    try: item, _ = await repo.create_report(user_id, **data.model_dump())
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    rows = await repo.list_reports(); row = next(row for row in rows if row[0].id == item.id)
    return report_out(*row)


@admin_router.get("/reports", response_model=list[CommunityReportOut])
async def reports(status: str | None = Query(None, pattern="^(pending|resolved|dismissed)$"), admin_id: int = Depends(auth_handler.require_permissions("community.moderate")), session: AsyncSession = Depends(get_session)):
    return [report_out(*row) for row in await CommunityRepository(session).list_reports(status)]


@admin_router.post("/polls/{poll_id}/featured", response_model=CommunityPollOut)
async def feature(poll_id: int, data: CommunityFeatureIn, request: Request, admin_id: int = Depends(auth_handler.require_permissions("community.moderate")), session: AsyncSession = Depends(get_session)):
    repo = CommunityRepository(session)
    try: await repo.set_featured(poll_id, data.is_featured)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    await SecurityRepository(session).audit(admin_user_id=admin_id, action="community.feature", target_type="community_poll", target_id=str(poll_id), detail=json.dumps(data.model_dump()), ip_address=request_ip(request))
    return await repo.poll(poll_id, admin_id, admin=True)


@admin_router.post("/reports/{report_id}/moderate", response_model=CommunityReportOut)
async def moderate(report_id: int, data: CommunityModerateIn, request: Request, admin_id: int = Depends(auth_handler.require_permissions("community.moderate")), session: AsyncSession = Depends(get_session)):
    repo = CommunityRepository(session)
    try: item = await repo.moderate_report(report_id, data.action, data.resolution)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    await SecurityRepository(session).audit(admin_user_id=admin_id, action=f"community.report.{data.action}", target_type=item.target_type, target_id=str(item.target_id), detail=json.dumps(data.model_dump(), ensure_ascii=False), ip_address=request_ip(request))
    rows = await repo.list_reports(); row = next(row for row in rows if row[0].id == item.id)
    return report_out(*row)
