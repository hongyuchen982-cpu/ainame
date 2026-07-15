# dependencies.py

# ... 这里是你之前写的 get_session 等数据库相关的代码 ...

from core.mailtool import create_mail_instance
from fastapi_mail import FastMail

# 追加到下面：定义获取邮箱实例的依赖
async def get_email() -> FastMail:
    return create_mail_instance()

from typing import AsyncGenerator  # 顶部加上这行
from models import AsyncSessionFactory
from sqlalchemy.ext.asyncio.session import AsyncSession

async def get_session() -> AsyncGenerator[AsyncSession, None]:  # ← 修改这里
    session = AsyncSessionFactory()
    try:
        yield session
    finally:
        await session.close()
