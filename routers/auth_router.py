import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi_mail import FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from core.redistools import get_redis
from dependencies import get_email, get_session
from repository.credit_repo import CreditRepository
from repository.security_repo import SecurityRepository
from repository.user_repo import UserRepository
from schemas import ResponseOut
from schemas.user_schemas import (
    AccessTokenOut,
    LoginIn,
    LoginOut,
    PasswordResetCodeIn,
    PasswordResetConfirmIn,
    RegisterIn,
    TokenVerifyOut,
    UserCreateSchema,
)

router = APIRouter(prefix="/auth", tags=["认证"])
auth_handler = AuthHandler()
SEND_LIMIT = 3
SEND_WINDOW_SECONDS = 600
VERIFY_LIMIT = 5
VERIFY_WINDOW_SECONDS = 600
LOGIN_LIMIT = 8
LOGIN_WINDOW_SECONDS = 900

RATE_LIMIT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return current
"""

CONSUME_CODE_SCRIPT = """
local saved = redis.call('GET', KEYS[1])
if not saved then return -1 end
if saved ~= ARGV[1] then return 0 end
redis.call('DEL', KEYS[1])
return 1
"""


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


async def increment_rate_limit(
    redis: Redis,
    key: str,
    *,
    limit: int,
    window_seconds: int,
) -> int:
    current = int(await redis.eval(RATE_LIMIT_SCRIPT, 1, key, window_seconds))
    if current > limit:
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    return current


async def ensure_not_rate_limited(redis: Redis, key: str, limit: int) -> None:
    if int(await redis.get(key) or 0) >= limit:
        raise HTTPException(status_code=429, detail="尝试次数过多，请稍后再试")


async def consume_email_code(redis: Redis, key: str, code: str) -> bool:
    return int(await redis.eval(CONSUME_CODE_SCRIPT, 1, key, code)) == 1


async def send_email_code(
    *,
    mail: FastMail,
    redis: Redis,
    key: str,
    email: str,
    code: str,
    subject: str,
) -> None:
    await redis.set(key, code, ex=300)
    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=f"您的验证码为：{code}，5 分钟内有效。请勿向他人泄露。",
        subtype=MessageType.plain,
    )
    try:
        await mail.send_message(message)
    except Exception as exc:
        await redis.delete(key)
        raise HTTPException(status_code=500, detail="邮件发送失败") from exc


@router.get("/code", response_model=ResponseOut)
async def get_email_code(
    request: Request,
    email: EmailStr = Query(...),
    mail: FastMail = Depends(get_email),
    redis: Redis = Depends(get_redis),
):
    normalized_email = str(email).lower()
    ip_address = client_ip(request)
    await increment_rate_limit(
        redis, f"rate:register-code:email:{normalized_email}",
        limit=SEND_LIMIT, window_seconds=SEND_WINDOW_SECONDS,
    )
    await increment_rate_limit(
        redis, f"rate:register-code:ip:{ip_address}",
        limit=SEND_LIMIT, window_seconds=SEND_WINDOW_SECONDS,
    )
    code = f"{secrets.randbelow(1000000):06d}"
    await send_email_code(
        mail=mail,
        redis=redis,
        key=f"register:code:{normalized_email}",
        email=normalized_email,
        code=code,
        subject="【一念 AI】注册验证码",
    )
    return {"result": "success", "message": "验证码已发送至您的邮箱"}


@router.post("/register", response_model=ResponseOut)
async def register(
    data: RegisterIn,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    email = str(data.email).lower()
    user_repo = UserRepository(session)
    if await user_repo.email_is_exist(email):
        raise HTTPException(status_code=400, detail="该邮箱已经存在")

    attempt_key = f"rate:register-verify:{email}"
    await ensure_not_rate_limited(redis, attempt_key, VERIFY_LIMIT)
    redis_key = f"register:code:{email}"
    if not await consume_email_code(redis, redis_key, data.code):
        await increment_rate_limit(
            redis, attempt_key, limit=VERIFY_LIMIT,
            window_seconds=VERIFY_WINDOW_SECONDS,
        )
        raise HTTPException(status_code=400, detail="验证码错误")

    try:
        async with session.begin():
            user = await user_repo.create_in_transaction(UserCreateSchema(
                email=email,
                username=data.username,
                password=data.password,
            ))
            await CreditRepository(session).create_register_credit_in_transaction(
                user.id, gift_count=3
            )
            await SecurityRepository(session).assign_default_role_in_transaction(user.id)
            from repository.growth_repo import GrowthRepository
            await GrowthRepository(session).bind_registration_in_transaction(
                user.id, data.invite_code
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="该邮箱已经存在") from exc
    await redis.delete(attempt_key)
    return {"result": "success", "message": "注册成功"}


@router.post("/login", response_model=LoginOut)
async def login(
    data: LoginIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    email = str(data.email).lower()
    ip_address = client_ip(request)
    email_rate_key = f"rate:login:email:{email}"
    ip_rate_key = f"rate:login:ip:{ip_address}"
    await ensure_not_rate_limited(redis, email_rate_key, LOGIN_LIMIT)
    await ensure_not_rate_limited(redis, ip_rate_key, LOGIN_LIMIT)
    user_agent = request.headers.get("user-agent", "")
    user_repo = UserRepository(session)
    security_repo = SecurityRepository(session)
    user = await user_repo.get_by_email(email)

    if user is None or not user.check_password(data.password):
        await security_repo.record_login(
            email=email,
            user_id=user.id if user else None,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            failure_reason="邮箱或密码错误",
        )
        await increment_rate_limit(
            redis, email_rate_key, limit=LOGIN_LIMIT,
            window_seconds=LOGIN_WINDOW_SECONDS,
        )
        await increment_rate_limit(
            redis, ip_rate_key, limit=LOGIN_LIMIT,
            window_seconds=LOGIN_WINDOW_SECONDS,
        )
        raise HTTPException(status_code=400, detail="邮箱或密码错误")
    if user.status != "active":
        await security_repo.record_login(
            email=email,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            failure_reason="账号已被冻结",
        )
        raise HTTPException(status_code=403, detail="账号已被冻结，请联系管理员")

    await redis.delete(email_rate_key, ip_rate_key)

    refresh_jti = str(uuid4())
    device = await security_repo.create_device(
        user_id=user.id,
        user_agent=user_agent,
        ip_address=ip_address,
        refresh_jti=refresh_jti,
    )
    tokens = auth_handler.encode_login_token(
        user_id=user.id,
        token_version=user.token_version,
        device_id=device.id,
        refresh_jti=refresh_jti,
    )
    await security_repo.record_login(
        email=email,
        user_id=user.id,
        device_id=device.id,
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
    )
    roles = await security_repo.get_role_codes(user.id)
    permissions = sorted(await security_repo.get_permission_codes(user.id))
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "status": user.status,
            "roles": roles,
            "permissions": permissions,
        },
        **tokens,
    }


@router.get("/verify-access", response_model=TokenVerifyOut)
async def verify_access_token(
    user_id: int = Depends(auth_handler.auth_access_dependency),
):
    return {"message": "Access Token 验证成功", "user_id": user_id}


@router.post("/refresh", response_model=AccessTokenOut)
async def refresh_access_token(
    payload: dict = Depends(auth_handler.auth_refresh_dependency),
    session: AsyncSession = Depends(get_session),
):
    user = await UserRepository(session).get_by_id(payload["user_id"])
    refresh_jti = str(uuid4())
    device = await SecurityRepository(session).rotate_refresh_token(
        payload.get("device_id", ""),
        payload["user_id"],
        payload.get("jti", ""),
        refresh_jti,
    )
    if user is None or device is None:
        raise HTTPException(status_code=401, detail="登录设备已失效")
    return auth_handler.encode_login_token(
        user_id=user.id,
        token_version=user.token_version,
        device_id=device.id,
        refresh_jti=refresh_jti,
    )


@router.post("/logout", response_model=ResponseOut)
async def logout(
    payload: dict = Depends(auth_handler.auth_access_payload_dependency),
    session: AsyncSession = Depends(get_session),
):
    await SecurityRepository(session).revoke_device(
        payload.get("device_id", ""),
        payload["user_id"],
    )
    return {"result": "success", "message": "已安全退出"}


@router.post("/password-reset/code", response_model=ResponseOut)
async def password_reset_code(
    data: PasswordResetCodeIn,
    request: Request,
    mail: FastMail = Depends(get_email),
    redis: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_session),
):
    email = str(data.email).lower()
    ip_address = client_ip(request)
    await increment_rate_limit(
        redis, f"rate:reset-code:email:{email}",
        limit=SEND_LIMIT, window_seconds=SEND_WINDOW_SECONDS,
    )
    await increment_rate_limit(
        redis, f"rate:reset-code:ip:{ip_address}",
        limit=SEND_LIMIT, window_seconds=SEND_WINDOW_SECONDS,
    )
    user = await UserRepository(session).get_by_email(email)
    if user:
        code = f"{secrets.randbelow(1000000):06d}"
        await send_email_code(
            mail=mail,
            redis=redis,
            key=f"password-reset:code:{email}",
            email=email,
            code=code,
            subject="【一念 AI】密码重置验证码",
        )
    return {"result": "success", "message": "如果该邮箱已注册，验证码将发送至邮箱"}


@router.post("/password-reset/confirm", response_model=ResponseOut)
async def password_reset_confirm(
    data: PasswordResetConfirmIn,
    redis: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_session),
):
    email = str(data.email).lower()
    attempt_key = f"rate:password-reset-verify:{email}"
    await ensure_not_rate_limited(redis, attempt_key, VERIFY_LIMIT)
    redis_key = f"password-reset:code:{email}"
    if not await consume_email_code(redis, redis_key, data.code):
        await increment_rate_limit(
            redis, attempt_key, limit=VERIFY_LIMIT,
            window_seconds=VERIFY_WINDOW_SECONDS,
        )
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(email)
    if user is None:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")
    await user_repo.change_password(user.id, data.new_password)
    await SecurityRepository(session).revoke_all_devices(user.id)
    await redis.delete(attempt_key)
    return {"result": "success", "message": "密码已重置，请重新登录"}
