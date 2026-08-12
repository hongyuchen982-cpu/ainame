import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from dependencies import get_session
from repository.security_repo import SecurityRepository
from repository.credit_repo import CreditRepository
from repository.admin_dashboard_repo import AdminDashboardRepository
from repository.user_repo import UserRepository
from schemas.user_schemas import (
    AdminUserOut,
    AuditLogOut,
    PermissionOut,
    RoleCreateIn,
    RoleOut,
    RolePermissionsIn,
    UserRolesIn,
    UserStatusIn,
)
from schemas.credit_schemas import AdminCreditAccountOut, AdminCreditAdjustIn
from schemas.admin_schemas import AdminDashboardOut, AdminProjectOut

router = APIRouter(prefix="/admin", tags=["运营后台·权限"])
auth_handler = AuthHandler()


@router.get("/dashboard", response_model=AdminDashboardOut)
async def dashboard(
    admin_id: int = Depends(auth_handler.require_permissions("dashboard.read")),
    session: AsyncSession = Depends(get_session),
):
    return await AdminDashboardRepository(session).summary()


@router.get("/projects", response_model=list[AdminProjectOut])
async def list_projects(
    status: str | None = Query(None, pattern="^(draft|generated|selected|archived)$"),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_id: int = Depends(auth_handler.require_permissions("projects.manage")),
    session: AsyncSession = Depends(get_session),
):
    return await AdminDashboardRepository(session).projects(status, limit, offset)


def request_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


async def admin_user_response(user, session: AsyncSession) -> dict:
    roles = await SecurityRepository(session).get_role_codes(user.id)
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "status": user.status,
        "roles": roles,
        "created_at": user.created_at,
    }


async def role_response(role, session: AsyncSession) -> dict:
    permissions = await SecurityRepository(session).get_role_permission_codes(role.id)
    return {
        "id": role.id,
        "code": role.code,
        "name": role.name,
        "description": role.description,
        "is_system": role.is_system,
        "permissions": permissions,
    }


@router.get("/users", response_model=list[AdminUserOut])
async def list_users(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_id: int = Depends(auth_handler.require_permissions("users.read")),
    session: AsyncSession = Depends(get_session),
):
    users = await UserRepository(session).list_users(limit=limit, offset=offset)
    return [await admin_user_response(user, session) for user in users]


@router.patch("/users/{user_id}/status", response_model=AdminUserOut)
async def update_user_status(
    user_id: int,
    data: UserStatusIn,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("users.freeze")),
    session: AsyncSession = Depends(get_session),
):
    if user_id == admin_id and data.status == "frozen":
        raise HTTPException(status_code=400, detail="不能冻结自己的管理员账号")
    user_repo = UserRepository(session)
    security_repo = SecurityRepository(session)
    async with session.begin():
        user = await user_repo.set_status_in_transaction(user_id, data.status)
        if user is None:
            raise HTTPException(status_code=404, detail="用户不存在")
        await security_repo.revoke_all_devices_in_transaction(user_id)
        await security_repo.audit_in_transaction(
            admin_user_id=admin_id,
            action=f"user.{data.status}",
            target_type="user",
            target_id=str(user_id),
            detail=json.dumps({"status": data.status}, ensure_ascii=False),
            ip_address=request_ip(request),
        )
    return await admin_user_response(user, session)


@router.put("/users/{user_id}/roles", response_model=AdminUserOut)
async def update_user_roles(
    user_id: int,
    data: UserRolesIn,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("users.roles")),
    session: AsyncSession = Depends(get_session),
):
    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user_id == admin_id and "admin" not in data.roles:
        raise HTTPException(status_code=400, detail="不能移除自己的管理员角色")
    security_repo = SecurityRepository(session)
    try:
        async with session.begin():
            roles = await security_repo.replace_user_roles_in_transaction(
                user_id, data.roles
            )
            await security_repo.revoke_all_devices_in_transaction(user_id)
            await security_repo.audit_in_transaction(
                admin_user_id=admin_id,
                action="user.roles.update",
                target_type="user",
                target_id=str(user_id),
                detail=json.dumps({"roles": roles}, ensure_ascii=False),
                ip_address=request_ip(request),
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await admin_user_response(user, session)


@router.get("/roles", response_model=list[RoleOut])
async def list_roles(
    admin_id: int = Depends(auth_handler.require_permissions("roles.manage")),
    session: AsyncSession = Depends(get_session),
):
    roles = await SecurityRepository(session).list_roles()
    return [await role_response(role, session) for role in roles]


@router.get("/permissions", response_model=list[PermissionOut])
async def list_permissions(
    admin_id: int = Depends(auth_handler.require_permissions("roles.manage")),
    session: AsyncSession = Depends(get_session),
):
    return await SecurityRepository(session).list_permissions()


@router.post("/roles", response_model=RoleOut)
async def create_role(
    data: RoleCreateIn,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("roles.manage")),
    session: AsyncSession = Depends(get_session),
):
    security_repo = SecurityRepository(session)
    try:
        async with session.begin():
            role = await security_repo.create_role_in_transaction(
                code=data.code,
                name=data.name,
                description=data.description,
                permission_codes=data.permissions,
            )
            await security_repo.audit_in_transaction(
                admin_user_id=admin_id,
                action="role.create",
                target_type="role",
                target_id=role.code,
                detail=data.model_dump_json(),
                ip_address=request_ip(request),
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await role_response(role, session)


@router.put("/roles/{role_code}/permissions", response_model=RoleOut)
async def update_role_permissions(
    role_code: str,
    data: RolePermissionsIn,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("roles.manage")),
    session: AsyncSession = Depends(get_session),
):
    security_repo = SecurityRepository(session)
    try:
        async with session.begin():
            role = await security_repo.replace_role_permissions_in_transaction(
                role_code,
                data.permissions,
            )
            if role is None:
                raise HTTPException(status_code=404, detail="角色不存在")
            await security_repo.audit_in_transaction(
                admin_user_id=admin_id,
                action="role.permissions.update",
                target_type="role",
                target_id=role_code,
                detail=data.model_dump_json(),
                ip_address=request_ip(request),
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await role_response(role, session)


@router.get("/audit-logs", response_model=list[AuditLogOut])
async def list_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    admin_id: int = Depends(auth_handler.require_permissions("audit.read")),
    session: AsyncSession = Depends(get_session),
):
    return await SecurityRepository(session).list_audit_logs(limit)


@router.get("/credits", response_model=list[AdminCreditAccountOut])
async def list_credit_accounts(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_id: int = Depends(auth_handler.require_permissions("credits.manage")),
    session: AsyncSession = Depends(get_session),
):
    rows = await CreditRepository(session).list_admin_accounts(
        limit=limit, offset=offset
    )
    return [
        {
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "balance": account.balance,
            "total_used": account.total_used,
            "total_recharge": account.total_recharge,
        }
        for account, user in rows
    ]


@router.post("/users/{user_id}/credits", response_model=AdminCreditAccountOut)
async def adjust_user_credit(
    user_id: int,
    data: AdminCreditAdjustIn,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("credits.manage")),
    session: AsyncSession = Depends(get_session),
):
    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    try:
        async with session.begin():
            account = await CreditRepository(session).adjust_credit_in_transaction(
                user_id=user_id,
                change_count=data.change_count,
                remark=data.remark,
                operation_id=data.operation_id,
            )
            await SecurityRepository(session).audit_in_transaction(
                admin_user_id=admin_id,
                action="credit.adjust",
                target_type="user_credit",
                target_id=str(user_id),
                detail=data.model_dump_json(),
                ip_address=request_ip(request),
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "user_id": user.id,
        "email": user.email,
        "username": user.username,
        "balance": account.balance,
        "total_used": account.total_used,
        "total_recharge": account.total_recharge,
    }
