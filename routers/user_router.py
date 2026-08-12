from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from dependencies import get_session
from repository.security_repo import SecurityRepository
from repository.dashboard_repo import UserDashboardRepository
from repository.user_repo import UserRepository
from schemas import ResponseOut
from schemas.user_schemas import (
    ChangePasswordIn,
    DeviceOut,
    UserDashboardOut,
    LoginRecordOut,
    ProfileUpdateIn,
    UserSchema,
)

router = APIRouter(prefix="/users", tags=["用户中心"])
auth_handler = AuthHandler()
AVATAR_DIR = Path(__file__).resolve().parents[1] / "static" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_AVATARS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024


def valid_image_signature(content_type: str, content: bytes) -> bool:
    if content_type == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/webp":
        return len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
    return False


async def profile_response(user, session: AsyncSession) -> dict:
    security_repo = SecurityRepository(session)
    roles = await security_repo.get_role_codes(user.id)
    permissions = sorted(await security_repo.get_permission_codes(user.id))
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "status": user.status,
        "roles": roles,
        "permissions": permissions,
    }


@router.get("/me", response_model=UserSchema)
async def get_my_profile(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return await profile_response(user, session)


@router.get("/me/dashboard", response_model=UserDashboardOut)
async def get_my_dashboard(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await UserDashboardRepository(session).get(user_id)


@router.patch("/me", response_model=UserSchema)
async def update_my_profile(
    data: ProfileUpdateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    if data.username is None and data.avatar_url is None:
        raise HTTPException(status_code=400, detail="没有需要修改的资料")
    user = await UserRepository(session).update_profile(
        user_id,
        username=data.username,
        avatar_url=data.avatar_url,
    )
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return await profile_response(user, session)


@router.post("/me/avatar", response_model=UserSchema)
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    suffix = ALLOWED_AVATARS.get(file.content_type or "")
    if suffix is None:
        raise HTTPException(status_code=400, detail="头像仅支持 JPG、PNG、WebP")
    content = await file.read(MAX_AVATAR_SIZE + 1)
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="头像不能超过 2MB")
    if not content:
        raise HTTPException(status_code=400, detail="头像文件为空")
    if not valid_image_signature(file.content_type or "", content):
        raise HTTPException(status_code=400, detail="头像文件内容与图片格式不匹配")

    file_name = f"{user_id}_{uuid4().hex}{suffix}"
    (AVATAR_DIR / file_name).write_bytes(content)
    user = await UserRepository(session).update_profile(
        user_id,
        avatar_url=f"/static/avatars/{file_name}",
    )
    return await profile_response(user, session)


@router.post("/me/password", response_model=ResponseOut)
async def change_my_password(
    data: ChangePasswordIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if user is None or not user.check_password(data.current_password):
        raise HTTPException(status_code=400, detail="当前密码错误")
    await user_repo.change_password(user_id, data.new_password)
    await SecurityRepository(session).revoke_all_devices(user_id)
    return {"result": "success", "message": "密码修改成功，请重新登录"}


@router.get("/me/devices", response_model=list[DeviceOut])
async def list_my_devices(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await SecurityRepository(session).list_devices(user_id)


@router.delete("/me/devices/{device_id}", response_model=ResponseOut)
async def revoke_my_device(
    device_id: str,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    if not await SecurityRepository(session).revoke_device(device_id, user_id):
        raise HTTPException(status_code=404, detail="登录设备不存在")
    return {"result": "success", "message": "设备登录已撤销"}


@router.get("/me/login-records", response_model=list[LoginRecordOut])
async def list_my_login_records(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await SecurityRepository(session).list_login_records(user_id)
