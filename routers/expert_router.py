import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from dependencies import get_session
from repository.expert_repo import ExpertRepository
from repository.security_repo import SecurityRepository
from routers.admin_router import request_ip
from schemas.expert_schemas import (
    AdminExpertProfileOut, ExpertApplyIn, ExpertDeliveryIn, ExpertOrderCreateIn,
    ExpertOrderOut, ExpertPackageIn, ExpertPackageOut, ExpertPackageStatusIn,
    ExpertProfileOut, ExpertReviewApplicationIn, ExpertReviewIn, ExpertSettlementOut,
)


router = APIRouter(prefix="/experts", tags=["专家服务"])
expert_router = APIRouter(prefix="/expert", tags=["专家工作台"])
admin_router = APIRouter(prefix="/admin/experts", tags=["运营后台·专家服务"])
auth_handler = AuthHandler()


def profile_out(item):
    return {key: getattr(item, key) for key in ("id", "user_id", "display_name", "title", "specialties", "bio", "experience_years", "portfolio", "status", "review_note", "rating_average", "rating_count", "created_at", "reviewed_at")}


def package_out(package, profile):
    return {"id": package.id, "expert_id": profile.id, "expert_name": profile.display_name, "expert_title": profile.title, "expert_rating": profile.rating_average, "expert_rating_count": profile.rating_count, "name": package.name, "description": package.description, "price": package.price, "delivery_days": package.delivery_days, "revision_count": package.revision_count, "is_active": package.is_active, "created_at": package.created_at}


def order_out(order, user, delivery=None, review=None):
    delivery_data = None if delivery is None else {"id": delivery.id, "title": delivery.title, "content": delivery.content, "attachment_url": delivery.attachment_url, "created_at": delivery.created_at}
    review_data = None if review is None else {"id": review.id, "rating": review.rating, "content": review.content, "created_at": review.created_at}
    return {"id": order.id, "order_no": order.order_no, "user_id": order.user_id, "customer_name": user.username, "expert_id": order.expert_id, "expert_name": order.expert_name, "package_id": order.package_id, "package_name": order.package_name, "project_id": order.project_id, "amount": order.amount, "requirement": order.requirement, "status": order.status, "created_at": order.created_at, "accepted_at": order.accepted_at, "delivered_at": order.delivered_at, "completed_at": order.completed_at, "delivery": delivery_data, "review": review_data}


def settlement_out(item, order, profile):
    return {"id": item.id, "order_id": order.id, "order_no": order.order_no, "expert_id": profile.id, "expert_name": profile.display_name, "gross_amount": item.gross_amount, "platform_fee": item.platform_fee, "net_amount": item.net_amount, "status": item.status, "settled_at": item.settled_at, "created_at": item.created_at}


@router.post("/apply", response_model=ExpertProfileOut)
async def apply(data: ExpertApplyIn, user_id: int = Depends(auth_handler.auth_access_dependency), session: AsyncSession = Depends(get_session)):
    try: return profile_out(await ExpertRepository(session).apply(user_id, **data.model_dump()))
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc


@router.get("/me", response_model=ExpertProfileOut | None)
async def my_profile(user_id: int = Depends(auth_handler.auth_access_dependency), session: AsyncSession = Depends(get_session)):
    item = await ExpertRepository(session).my_profile(user_id)
    return profile_out(item) if item else None


@router.get("/packages", response_model=list[ExpertPackageOut])
async def packages(session: AsyncSession = Depends(get_session)):
    return [package_out(package, profile) for package, profile in await ExpertRepository(session).list_packages(public=True)]


@router.post("/orders", response_model=ExpertOrderOut)
async def create_order(data: ExpertOrderCreateIn, user_id: int = Depends(auth_handler.auth_access_dependency), session: AsyncSession = Depends(get_session)):
    repo = ExpertRepository(session)
    try: order, _ = await repo.create_order(user_id, data.package_id, data.project_id, data.requirement, data.client_request_id)
    except (ValueError, LookupError) as exc: raise HTTPException(400 if isinstance(exc, ValueError) else 404, str(exc)) from exc
    rows = await repo.list_orders(user_id=user_id); row = next(row for row in rows if row[0].id == order.id); return order_out(*row)


@router.get("/orders", response_model=list[ExpertOrderOut])
async def my_orders(user_id: int = Depends(auth_handler.auth_access_dependency), session: AsyncSession = Depends(get_session)):
    return [order_out(*row) for row in await ExpertRepository(session).list_orders(user_id=user_id)]


@router.post("/orders/{order_id}/review", response_model=ExpertOrderOut)
async def review_order(order_id: int, data: ExpertReviewIn, user_id: int = Depends(auth_handler.auth_access_dependency), session: AsyncSession = Depends(get_session)):
    repo = ExpertRepository(session)
    try: await repo.review_order(order_id, user_id, data.rating, data.content)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    row = next(row for row in await repo.list_orders(user_id=user_id) if row[0].id == order_id); return order_out(*row)


@expert_router.get("/packages", response_model=list[ExpertPackageOut])
async def own_packages(user_id: int = Depends(auth_handler.require_permissions("expert.work")), session: AsyncSession = Depends(get_session)):
    return [package_out(package, profile) for package, profile in await ExpertRepository(session).list_packages(user_id=user_id)]


@expert_router.post("/packages", response_model=ExpertPackageOut)
async def create_package(data: ExpertPackageIn, user_id: int = Depends(auth_handler.require_permissions("expert.work")), session: AsyncSession = Depends(get_session)):
    try: package, profile = await ExpertRepository(session).create_package(user_id, **data.model_dump()); return package_out(package, profile)
    except PermissionError as exc: raise HTTPException(403, str(exc)) from exc


@expert_router.post("/packages/{package_id}/status", response_model=ExpertPackageOut)
async def package_status(package_id: int, data: ExpertPackageStatusIn, user_id: int = Depends(auth_handler.require_permissions("expert.work")), session: AsyncSession = Depends(get_session)):
    try: package, profile = await ExpertRepository(session).set_package_status(package_id, user_id, data.is_active); return package_out(package, profile)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc


@expert_router.get("/orders", response_model=list[ExpertOrderOut])
async def expert_orders(user_id: int = Depends(auth_handler.require_permissions("expert.work")), session: AsyncSession = Depends(get_session)):
    return [order_out(*row) for row in await ExpertRepository(session).list_orders(expert_user_id=user_id)]


@expert_router.post("/orders/{order_id}/accept", response_model=ExpertOrderOut)
async def accept(order_id: int, user_id: int = Depends(auth_handler.require_permissions("expert.work")), session: AsyncSession = Depends(get_session)):
    repo = ExpertRepository(session)
    try: await repo.accept(order_id, user_id)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    row = next(row for row in await repo.list_orders(expert_user_id=user_id) if row[0].id == order_id); return order_out(*row)


@expert_router.post("/orders/{order_id}/deliver", response_model=ExpertOrderOut)
async def deliver(order_id: int, data: ExpertDeliveryIn, user_id: int = Depends(auth_handler.require_permissions("expert.work")), session: AsyncSession = Depends(get_session)):
    repo = ExpertRepository(session)
    try: await repo.deliver(order_id, user_id, **data.model_dump())
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    row = next(row for row in await repo.list_orders(expert_user_id=user_id) if row[0].id == order_id); return order_out(*row)


@expert_router.get("/settlements", response_model=list[ExpertSettlementOut])
async def expert_settlements(user_id: int = Depends(auth_handler.require_permissions("expert.work")), session: AsyncSession = Depends(get_session)):
    return [settlement_out(*row) for row in await ExpertRepository(session).list_settlements(expert_user_id=user_id)]


@admin_router.get("/applications", response_model=list[AdminExpertProfileOut])
async def applications(status: str | None = Query(None, pattern="^(pending|approved|rejected)$"), admin_id: int = Depends(auth_handler.require_permissions("experts.manage")), session: AsyncSession = Depends(get_session)):
    return [{**profile_out(profile), "username": user.username, "user_email": user.email} for profile, user in await ExpertRepository(session).list_applications(status)]


@admin_router.post("/applications/{profile_id}/review", response_model=ExpertProfileOut)
async def review_application(profile_id: int, data: ExpertReviewApplicationIn, request: Request, admin_id: int = Depends(auth_handler.require_permissions("experts.manage")), session: AsyncSession = Depends(get_session)):
    repo = ExpertRepository(session)
    try: profile = await repo.review_application(profile_id, data.status, data.review_note)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    await SecurityRepository(session).audit(admin_user_id=admin_id, action=f"expert.{data.status}", target_type="expert_profile", target_id=str(profile_id), detail=json.dumps(data.model_dump(), ensure_ascii=False), ip_address=request_ip(request)); return profile_out(profile)


@admin_router.get("/orders", response_model=list[ExpertOrderOut])
async def all_orders(admin_id: int = Depends(auth_handler.require_permissions("experts.manage")), session: AsyncSession = Depends(get_session)):
    return [order_out(*row) for row in await ExpertRepository(session).list_orders(all_rows=True)]


@admin_router.get("/settlements", response_model=list[ExpertSettlementOut])
async def all_settlements(admin_id: int = Depends(auth_handler.require_permissions("settlements.manage")), session: AsyncSession = Depends(get_session)):
    return [settlement_out(*row) for row in await ExpertRepository(session).list_settlements()]


@admin_router.post("/settlements/{settlement_id}/settle", response_model=ExpertSettlementOut)
async def settle(settlement_id: int, request: Request, admin_id: int = Depends(auth_handler.require_permissions("settlements.manage")), session: AsyncSession = Depends(get_session)):
    repo = ExpertRepository(session)
    try: item = await repo.settle(settlement_id)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    rows = await repo.list_settlements(); row = next(row for row in rows if row[0].id == item.id)
    await SecurityRepository(session).audit(admin_user_id=admin_id, action="expert.settlement.settle", target_type="expert_settlement", target_id=str(settlement_id), detail="{}", ip_address=request_ip(request)); return settlement_out(*row)
