import asyncio
import os
import sys

from dotenv import load_dotenv
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

load_dotenv()

DB_URI = os.getenv("LANGGRAPH_DB_URI")

if not DB_URI:
    raise RuntimeError(
        "没有读取到 LANGGRAPH_DB_URI，请检查 .env 文件"
    )

async def setup_memory_db():
    print("正在连接 PostgreSQL...")
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as saver:
        await saver.setup()
        print("✅ PostgreSQL 记忆持久化数据表创建成功！")
if __name__ == "__main__":
# ⚠ 专治 Windows 下的异步兼容性报错
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(setup_memory_db())
