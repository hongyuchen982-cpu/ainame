from fastapi import APIRouter, Depends, HTTPException, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from core.brand_asset_service import (
    build_domain_matrix,
    build_validation_snapshot,
    generate_brand_asset_content,
)
from core.distributed_lock import OperationBusyError, distributed_operation_lock
from core.redistools import get_redis
from dependencies import get_session
from repository.brand_asset_repo import BrandAssetRepository
from repository.project_repo import NamingProjectRepository
from repository.selected_name_repo import SelectedNameRepository
from repository.validation_repo import NameValidationRepository
from schemas.brand_asset_schemas import (
    AdminBrandAssetOut,
    BrandAssetCreateIn,
    BrandAssetOut,
)


auth_handler = AuthHandler()
router = APIRouter(prefix="/brand-assets", tags=["品牌价值资产"])
admin_router = APIRouter(prefix="/admin/brand-assets", tags=["运营后台·品牌资产"])


@router.post("", response_model=BrandAssetOut)
async def create_brand_asset(
    data: BrandAssetCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    repository = BrandAssetRepository(session)
    existing = await repository.get_by_request(data.client_request_id, user_id)
    if existing is not None:
        return existing
    try:
        async with distributed_operation_lock(
            redis, f"lock:brand-asset:request:{user_id}:{data.client_request_id}"
        ):
            async with distributed_operation_lock(
                redis, f"lock:brand-asset:selection:{data.selected_name_id}"
            ):
                return await _create_brand_asset_locked(
                    data, user_id, session, repository
                )
    except OperationBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


async def _create_brand_asset_locked(
    data: BrandAssetCreateIn,
    user_id: int,
    session: AsyncSession,
    repository: BrandAssetRepository,
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
        raise HTTPException(status_code=400, detail="品牌价值资产仅支持企业/品牌名称")

    validation_repo = NameValidationRepository(session)
    if data.validation_id is not None:
        validation = await validation_repo.get_for_user(data.validation_id, user_id)
        if validation is None:
            raise HTTPException(status_code=404, detail="名称校验记录不存在")
        if validation.selected_name_id != selected.id:
            raise HTTPException(
                status_code=400, detail="名称校验记录与当前最终名称不匹配"
            )
    else:
        validation = await validation_repo.latest_for_selection(selected.id, user_id)

    conditions = {}
    if selected.project_id is not None:
        project = await NamingProjectRepository(session).get_for_user(
            selected.project_id, user_id
        )
        if project is not None:
            conditions = project.conditions or {}
    snapshot = build_validation_snapshot(validation)
    try:
        generated = await generate_brand_asset_content(
            name=selected.name,
            moral=selected.moral,
            reference=selected.reference,
            conditions=conditions,
            brief=data.brief,
            validation_snapshot=snapshot,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    result = generated.model_dump()
    risk_notes = result["risk_notes"]
    if validation is None:
        risk_notes.insert(
            0,
            {
                "category": "校验覆盖",
                "level": "unknown",
                "note": "尚未关联名称综合校验，域名、商标、企业重名和社交平台状态未知。",
                "action": "正式发布或投入设计前先执行名称综合校验，并咨询相应专业机构。",
            },
        )
    return await repository.create(
        user_id=user_id,
        selected_name_id=selected.id,
        project_id=selected.project_id,
        validation_id=validation.id if validation else None,
        client_request_id=data.client_request_id,
        name=selected.name,
        brief=data.brief,
        positioning=result["positioning"],
        slogans=result["slogans"],
        logo_concepts=result["logo_concepts"],
        visual_guidelines=result["visual_guidelines"],
        domain_matrix=build_domain_matrix(snapshot),
        risk_notes=risk_notes,
        validation_snapshot=snapshot,
    )


@router.get("", response_model=list[BrandAssetOut])
async def list_brand_assets(
    selected_name_id: int | None = Query(None, ge=1),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await BrandAssetRepository(session).list_for_user(user_id, selected_name_id)


@router.get("/{asset_id}", response_model=BrandAssetOut)
async def brand_asset_detail(
    asset_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    item = await BrandAssetRepository(session).get_for_user(asset_id, user_id)
    if item is None:
        raise HTTPException(status_code=404, detail="品牌资产不存在")
    return item


@admin_router.get("", response_model=list[AdminBrandAssetOut])
async def admin_list_brand_assets(
    admin_id: int = Depends(auth_handler.require_permissions("brand_assets.manage")),
    session: AsyncSession = Depends(get_session),
):
    rows = await BrandAssetRepository(session).list_all()
    return [
        {
            **BrandAssetOut.model_validate(item).model_dump(),
            "user_id": user.id,
            "user_email": user.email,
            "username": user.username,
        }
        for item, user in rows
    ]
