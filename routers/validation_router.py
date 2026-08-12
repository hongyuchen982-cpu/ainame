from fastapi import APIRouter, Depends, HTTPException, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from core.distributed_lock import OperationBusyError, distributed_operation_lock
from core.name_validation_service import run_name_validation
from core.redistools import get_redis
from dependencies import get_session
from repository.selected_name_repo import SelectedNameRepository
from repository.validation_repo import NameValidationRepository
from schemas.validation_schemas import (
    AdminNameValidationOut,
    NameValidationCreateIn,
    NameValidationOut,
)


auth_handler = AuthHandler()
router = APIRouter(prefix="/validations", tags=["名称校验"])
admin_router = APIRouter(prefix="/admin/validations", tags=["运营后台·名称校验"])


@router.post("", response_model=NameValidationOut)
async def create_validation(
    data: NameValidationCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    repository = NameValidationRepository(session)
    existing = await repository.get_by_request(data.client_request_id, user_id)
    if existing is not None:
        return existing
    try:
        async with distributed_operation_lock(
            redis, f"lock:validation:selection:{data.selected_name_id}"
        ):
            existing = await repository.get_by_request(data.client_request_id, user_id)
            if existing is not None:
                return existing
            selected = await SelectedNameRepository(session).get_for_user(
                data.selected_name_id, user_id
            )
            if selected is None:
                raise HTTPException(status_code=404, detail="最终名称不存在")
            if selected.category != "企业名":
                raise HTTPException(status_code=400, detail="当前阶段仅支持企业/品牌名称综合校验")
            result = await run_name_validation(
                selected.name, data.domain_stem, data.suffixes
            )
            return await repository.create(
                user_id=user_id,
                selected_name_id=selected.id,
                project_id=selected.project_id,
                client_request_id=data.client_request_id,
                name=selected.name,
                domain_stem=data.domain_stem,
                status=result["status"],
                domains=result["domains"],
                trademark=result["trademark"],
                company=result["company"],
                social=result["social"],
                risk_score=result["score"],
                risk_level=result["level"],
                coverage=result["coverage"],
                risk_summary=result["summary"],
            )
    except OperationBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[NameValidationOut])
async def list_validations(
    selected_name_id: int | None = Query(None, ge=1),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await NameValidationRepository(session).list_for_user(
        user_id, selected_name_id
    )


@router.get("/{validation_id}", response_model=NameValidationOut)
async def validation_detail(
    validation_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    item = await NameValidationRepository(session).get_for_user(validation_id, user_id)
    if item is None:
        raise HTTPException(status_code=404, detail="校验记录不存在")
    return item


@admin_router.get("", response_model=list[AdminNameValidationOut])
async def admin_list_validations(
    risk_level: str | None = Query(None),
    status: str | None = Query(None),
    admin_id: int = Depends(auth_handler.require_permissions("validations.manage")),
    session: AsyncSession = Depends(get_session),
):
    rows = await NameValidationRepository(session).list_all(risk_level, status)
    return [{
        **NameValidationOut.model_validate(item).model_dump(),
        "user_id": user.id,
        "user_email": user.email,
        "username": user.username,
    } for item, user in rows]
