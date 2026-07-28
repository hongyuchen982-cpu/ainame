import os
from datetime import datetime, timezone
import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
import settings

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")


class AuthHandler:
    security = HTTPBearer()
    algorithm = "HS256"

    def __init__(self):
        # 兼容处理，防止环境变量没读到导致 secret 为 None
        self.secret = JWT_SECRET_KEY or getattr(settings, "JWT_SECRET_KEY", "fallback_secret")
        if not self.secret:
            print("=== 警告：JWT_SECRET_KEY 为空，请检查 .env 文件！ ===")

    def _create_token(self, user_id: int, token_type: str, expires_delta):
        payload = {
            "user_id": user_id,
            "type": token_type,
            "exp": datetime.now(timezone.utc) + expires_delta,
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def encode_login_token(self, user_id: int):
        return {
            "access_token": self._create_token(
                user_id=user_id,
                token_type="access",
                expires_delta=settings.JWT_ACCESS_TOKEN_EXPIRES,
            ),
            "refresh_token": self._create_token(
                user_id=user_id,
                token_type="refresh",
                expires_delta=settings.JWT_REFRESH_TOKEN_EXPIRES,
            ),
        }

    def encode_update_token(self, user_id: int):
        return {
            "access_token": self._create_token(
                user_id=user_id,
                token_type="access",
                expires_delta=settings.JWT_ACCESS_TOKEN_EXPIRES,
            )
        }

    def _decode_token(self, token: str, token_type: str, status_code: int):
        try:
            print(f"=== 正在解密 Token (类型: {token_type}) ===")
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])

            if payload.get("type") != token_type:
                print(f"=== 报错：Token 类型不匹配，期望 {token_type}，实际是 {payload.get('type')} ===")
                raise HTTPException(status_code=status_code, detail="Token类型错误")

            user_id = int(payload["user_id"])
            print(f"=== Token 解密成功，User ID: {user_id} ===")
            return user_id

        except HTTPException as he:
            print(f"=== 拦截到 HTTPException: {he.detail} ===")
            raise he

        except jwt.ExpiredSignatureError:
            print("=== 报错：Token已过期 ===")
            raise HTTPException(status_code=status_code, detail="Token已过期")

        except jwt.InvalidTokenError as e:
            print(f"=== 报错：InvalidTokenError -> {e} (可能秘钥不匹配或 Token 损坏) ===")
            raise HTTPException(status_code=status_code, detail="Token无效")

        except Exception as e:
            print(f"=== 报错：未知异常 -> {type(e).__name__}: {e} ===")
            raise HTTPException(status_code=status_code, detail="Token解析失败")

    def decode_access_token(self, token: str):
        return self._decode_token(
            token=token,
            token_type="access",
            status_code=HTTP_403_FORBIDDEN,
        )

    def decode_refresh_token(self, token: str):
        return self._decode_token(
            token=token,
            token_type="refresh",
            status_code=HTTP_401_UNAUTHORIZED,
        )

    def auth_access_dependency(
        self,
        auth: HTTPAuthorizationCredentials = Security(security),
    ):
        print("=== 成功进入访问鉴权，收到的 Token 凭证前缀为 ===", auth.credentials[:15] if auth.credentials else "None")
        return self.decode_access_token(auth.credentials)

    def auth_refresh_dependency(
        self,
        auth: HTTPAuthorizationCredentials = Security(security),
    ):
        print("=== 成功进入刷新鉴权，收到的 Token 凭证前缀为 ===", auth.credentials[:15] if auth.credentials else "None")
        return self.decode_refresh_token(auth.credentials)