import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_session
from repository.package_repo import PackageRepository
from core.authtools import AuthHandler
from repository.security_repo import SecurityRepository
from schemas.package_schemas import (
    AdminPackageOut,
    PackageCreateIn,
    PackageOut,
    PackageSortIn,
    PackageStatusIn,
    PackageUpdateIn,
)


router = APIRouter(prefix="/package")
admin_router = APIRouter(prefix="/admin/packages", tags=["运营后台·套餐"])
auth_handler = AuthHandler()
@router.get("/list", response_model=list[PackageOut])


async def package_list(
    session: AsyncSession = Depends(get_session),
):
    package_repo = PackageRepository(session=session)
    packages = await package_repo.list_active()
    return packages


def request_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@admin_router.get("", response_model=list[AdminPackageOut])
async def admin_package_list(
    admin_id: int = Depends(auth_handler.require_permissions("packages.manage")),
    session: AsyncSession = Depends(get_session),
):
    return await PackageRepository(session).list_all()


@admin_router.post("", response_model=AdminPackageOut)
async def create_package(
    data: PackageCreateIn,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("packages.manage")),
    session: AsyncSession = Depends(get_session),
):
    async with session.begin():
        package = await PackageRepository(session).create_in_transaction(
            **data.model_dump()
        )
        await SecurityRepository(session).audit_in_transaction(
            admin_user_id=admin_id,
            action="package.create",
            target_type="package",
            target_id=str(package.id),
            detail=data.model_dump_json(),
            ip_address=request_ip(request),
        )
    return package


@admin_router.patch("/{package_id}", response_model=AdminPackageOut)
async def update_package(
    package_id: int,
    data: PackageUpdateIn,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("packages.manage")),
    session: AsyncSession = Depends(get_session),
):
    async with session.begin():
        package = await PackageRepository(session).update_in_transaction(
            package_id, data.model_dump(exclude_unset=True)
        )
        if package is None:
            raise HTTPException(status_code=404, detail="套餐不存在")
        await SecurityRepository(session).audit_in_transaction(
            admin_user_id=admin_id,
            action="package.update",
            target_type="package",
            target_id=str(package_id),
            detail=data.model_dump_json(exclude_unset=True),
            ip_address=request_ip(request),
        )
    return package


@admin_router.post("/{package_id}/status", response_model=AdminPackageOut)
async def set_package_status(
    package_id: int,
    data: PackageStatusIn,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("packages.manage")),
    session: AsyncSession = Depends(get_session),
):
    async with session.begin():
        package = await PackageRepository(session).set_status_in_transaction(
            package_id, data.is_active
        )
        if package is None:
            raise HTTPException(status_code=404, detail="套餐不存在")
        await SecurityRepository(session).audit_in_transaction(
            admin_user_id=admin_id,
            action="package.activate" if data.is_active else "package.deactivate",
            target_type="package",
            target_id=str(package_id),
            detail=json.dumps({"is_active": data.is_active}),
            ip_address=request_ip(request),
        )
    return package


@admin_router.put("/sort", response_model=list[AdminPackageOut])
async def sort_packages(
    data: PackageSortIn,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("packages.manage")),
    session: AsyncSession = Depends(get_session),
):
    try:
        async with session.begin():
            packages = await PackageRepository(session).sort_in_transaction(
                [item.model_dump() for item in data.items]
            )
            await SecurityRepository(session).audit_in_transaction(
                admin_user_id=admin_id,
                action="package.sort",
                target_type="package",
                target_id="batch",
                detail=data.model_dump_json(),
                ip_address=request_ip(request),
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return packages


@admin_router.delete("/{package_id}")
async def delete_package(
    package_id: int,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("packages.manage")),
    session: AsyncSession = Depends(get_session),
):
    try:
        async with session.begin():
            deleted = await PackageRepository(session).delete_in_transaction(package_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="套餐不存在")
            await SecurityRepository(session).audit_in_transaction(
                admin_user_id=admin_id,
                action="package.delete",
                target_type="package",
                target_id=str(package_id),
                detail="{}",
                ip_address=request_ip(request),
            )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"message": "套餐已删除"}
