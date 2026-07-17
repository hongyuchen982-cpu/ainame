import random
import string
from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import EmailStr
from fastapi_mail import FastMail, MessageSchema, MessageType
from redis.asyncio import Redis
# 如果你用的是 fastapi-mail，建议用 aiosmtplib 的异常
from aiosmtplib.errors import SMTPException, SMTPResponseException
from core.redistools import get_redis
# 下面这几个路径按你项目实际位置改
from dependencies import get_email
from schemas import ResponseOut


router = APIRouter(prefix="/auth")

@router.get("/code", response_model=ResponseOut)
async def get_email_code(email: Annotated[EmailStr, Query(...)],
mail: FastMail = Depends(get_email),
redis: Redis = Depends(get_redis)):
# 1.生成4位数验证码
    source = string.digits * 4
    code = ''.join(random.sample(source, 4))

 # 2.创建消息对象
    message = MessageSchema(
        subject="【ai起名字app】注册验证码",
        recipients=[email],
        body=f"您的验证码为：{code}，五分钟有效！",
        # subtype = 邮件正文是什么格式
        # MessageType.plain = 纯文本格式
        subtype=MessageType.plain
    )
    try:
        await redis.set(f"register:code:{email}", code, ex=300)
        await mail.send_message(message)
        return {"result": "success", "message": "验证码已发送至您的邮箱"}
    except (SMTPResponseException, SMTPException) as e:
        # 捕获SMTP具体错误并记录
        error_str = str(e)
        if "-1" in error_str and r"\x00" in error_str:
            print("⚠️ 忽略 QQ 邮箱 SMTP 关闭阶段的非标准响应（邮件已成功发送）")
            # 将邮箱和验证码存储到数据库中
            await redis.set(f"register:code:{email}", code, ex=300)
            return ResponseOut()
        else:
            # 捕获所有其他错误
            raise HTTPException(status_code=500, detail="邮件发送失败！")
        
from schemas.user_schemas import UserCreateSchema,RegisterIn
from repository.user_repo import UserRepository
from dependencies import get_session
from sqlalchemy.ext.asyncio.session import AsyncSession

@router.post("/register", response_model=ResponseOut)
async def register(
    data: RegisterIn,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    user_repo = UserRepository(session=session)
    # 1. 判断邮箱是否存在
    email_exist = await user_repo.email_is_exist(email=str(data.email))
    if email_exist:
        raise HTTPException(400, detail="该邮箱已经存在！")
    # 2. 校验收证码是否正确  
    redis_key = f"register:code:{data.email}"
    saved_code = await redis.get(redis_key)
    if not saved_code:
        # 如果 Redis 里没有，说明要么压根没发，要么过了 5 分钟已经自动过期删除了
        raise HTTPException(400, detail="验证码已过期或未发送！")

    if saved_code != str(data.code):
        raise HTTPException(400, detail="验证码错误！")
    # if not email_code_match:
    #     raise HTTPException(400, detail='邮箱或验证码错误！')
    try:
        await user_repo.create(UserCreateSchema(email=str(data.email),
            password=data.password, username=data.username))

        # 4. 安全防御：注册成功后，立刻删掉 Redis 里的验证码！
        # 防止有人拿着这个还没过期的验证码，去疯狂发恶意请求（防重放攻击）
        await redis.delete(redis_key)
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    return ResponseOut()

from core.authtools import AuthHandler
from schemas.user_schemas import LoginIn
from models.user import User
from schemas.user_schemas import LoginOut

auth_handler = AuthHandler()

@router.post(path='/login', response_model=LoginOut)
async def login(
    data: LoginIn,
    session: AsyncSession = Depends(get_session),
):
    # 1. 创建user_repo对象
    user_repo = UserRepository(session=session)
    # 2. 根据邮箱查找用户
    user: User | None = await user_repo.get_by_email(str(data.email))
    if not user:
        raise HTTPException(status_code=400, detail="该用户不存在！")
    if not user.check_password(data.password):
        raise HTTPException(status_code=400, detail="邮箱或密码错误！")
    # 3. 生成JWT Token
    tokens = auth_handler.encode_login_token(user.id)
    return {
        "user": user,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
	}


from schemas.user_schemas import AccessTokenOut, TokenVerifyOut

@router.get(
    path="/verify-access",
    response_model=TokenVerifyOut,
)
async def verify_access_token(
    user_id: int = Depends(
        auth_handler.auth_access_dependency
    ),
):
    return {
        "message": "Access Token验证成功",
        "user_id": user_id,
    }

@router.post(
    path="/refresh",
    response_model=AccessTokenOut,
)
async def refresh_access_token(
    user_id: int = Depends(
        auth_handler.auth_refresh_dependency
    ),
):
    return auth_handler.encode_update_token(user_id)