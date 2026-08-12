import redis.asyncio as aioredis
import os
from typing import AsyncGenerator
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
# 创建一个全局的 Redis 连接池
# decode_responses=True 会自动将拿到的 bytes 解码为 str，非常方便
redis_client = aioredis.from_url(
REDIS_URL, 
encoding="utf-8", 
decode_responses=True,
protocol=2    
)
# 定义一个依赖函数，供 FastAPI 路由使用
async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
# 直接返回 client，因为连接池会在后台自动管理连接
    yield redis_client
