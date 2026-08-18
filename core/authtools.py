import os
from datetime import datetime, timezone
from uuid import uuid4

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

import settings
from dependencies import get_session
from models.auth_models import UserDevice
from models.user import User
from repository.security_repo import SecurityRepository

load_dotenv()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")


class AuthHandler:
    security = HTTPBearer()
    algorithm = "HS256"

    def __init__(self):
        self.secret = JWT_SECRET_KEY or getattr(settings, "JWT_SECRET_KEY", "")
        if not self.secret:
            raise RuntimeError("JWT_SECRET_KEY 未配置")

    def _create_token(
        self,
        *,
        user_id: int,
        token_version: int,
        token_type: str,
        expires_delta,
        device_id: str,
        jti: str | None = None,
    ) -> str:
        payload = {
            "user_id": user_id,
            "ver": token_version,
            "type": token_type,
            "device_id": device_id,
            "jti": jti or str(uuid4()),
            "exp": datetime.now(timezone.utc) + expires_delta,
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def encode_login_token(
        self,
        *,
        user_id: int,
        token_version: int,
        device_id: str,
        refresh_jti: str,
    ) -> dict[str, str]:
        return {
            "access_token": self._create_token(
                user_id=user_id,
                token_version=token_version,
                token_type="access",
                expires_delta=settings.JWT_ACCESS_TOKEN_EXPIRES,
                device_id=device_id,
            ),
            "refresh_token": self._create_token(
                user_id=user_id,
                token_version=token_version,
                token_type="refresh",
                expires_delta=settings.JWT_REFRESH_TOKEN_EXPIRES,
                device_id=device_id,
                jti=refresh_jti,
            ),
        }

    def encode_update_token(
        self,
        *,
        user_id: int,
        token_version: int,
        device_id: str,
    ) -> dict[str, str]:
        return {
            "access_token": self._create_token(
                user_id=user_id,
                token_version=token_version,
                token_type="access",
                expires_delta=settings.JWT_ACCESS_TOKEN_EXPIRES,
                device_id=device_id,
            )
        }

    def _decode_token(self, token: str, token_type: str, status_code: int) -> dict:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                raise HTTPException(status_code=status_code, detail="Token 类型错误")
            payload["user_id"] = int(payload["user_id"])
            payload["ver"] = int(payload.get("ver", -1))
            return payload
        except HTTPException:
            raise
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(status_code=status_code, detail="Token 已过期") from exc
        except jwt.InvalidTokenError as exc:
            raise HTTPException(status_code=status_code, detail="Token 无效") from exc
        except Exception as exc:
            raise HTTPException(status_code=status_code, detail="Token 解析失败") from exc

    async def _validate_payload(
        self,
        payload: dict,
        session: AsyncSession,
        status_code: int,
    ) -> User:
        async with session.begin():
            user = await session.get(User, payload["user_id"])
            if user is None:
                raise HTTPException(status_code=status_code, detail="用户不存在")
            if user.status != "active":
                raise HTTPException(status_code=status_code, detail="账号已被冻结")
            if user.token_version != payload["ver"]:
                raise HTTPException(status_code=status_code, detail="登录状态已失效，请重新登录")

            device_id = payload.get("device_id", "")
            device = await session.get(UserDevice, device_id) if device_id else None
            if device is None or device.user_id != user.id or device.revoked_at is not None:
                raise HTTPException(status_code=status_code, detail="登录设备已失效，请重新登录")
            if payload.get("type") == "refresh" and device.refresh_jti != payload.get("jti"):
                raise HTTPException(status_code=status_code, detail="Refresh Token 已失效")
            return user

    async def auth_access_payload_dependency(
        self,
        auth: HTTPAuthorizationCredentials = Security(security),
        session: AsyncSession = Depends(get_session),
    ) -> dict:
        payload = self._decode_token(
            auth.credentials,
            "access",
            HTTP_401_UNAUTHORIZED,
        )
        await self._validate_payload(payload, session, HTTP_401_UNAUTHORIZED)
        return payload

    async def auth_access_dependency(
        self,
        auth: HTTPAuthorizationCredentials = Security(security),
        session: AsyncSession = Depends(get_session),
    ) -> int:
        payload = await self.auth_access_payload_dependency(auth, session)
        return payload["user_id"]

    async def auth_refresh_dependency(
        self,
        auth: HTTPAuthorizationCredentials = Security(security),
        session: AsyncSession = Depends(get_session),
    ) -> dict:
        payload = self._decode_token(
            auth.credentials,
            "refresh",
            HTTP_401_UNAUTHORIZED,
        )
        await self._validate_payload(payload, session, HTTP_401_UNAUTHORIZED)
        return payload

    def require_permissions(self, *required: str):
        async def dependency(
            user_id: int = Depends(self.auth_access_dependency),
            session: AsyncSession = Depends(get_session),
        ) -> int:
            permissions = await SecurityRepository(session).get_permission_codes(user_id)
            missing = set(required) - permissions
            if missing:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail=f"缺少权限：{', '.join(sorted(missing))}",
                )
            return user_id

        return dependency
