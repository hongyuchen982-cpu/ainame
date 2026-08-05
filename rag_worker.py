import asyncio
import json
import os
import sys

import aio_pika
from dotenv import load_dotenv

from core.rag_service import process_and_store_file

load_dotenv()

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
QUEUE_NAME = "rag_document_queue"
async def process_message(message: aio_pika.IncomingMessage):
    """处理接收到的单条排队任务"""
    async with message.process():
        # 1. 拆解包裹
        task_data = json.loads(message.body.decode("utf-8"))
        user_id = task_data.get("user_id")
        file_path = task_data.get("file_path")

        print(f"📦 [Worker 接单] 开始解析用户 {user_id} 的文件: {file_path}")

        try:
            # 2. 执行原有的 RAG 向量化入库逻辑
            process_and_store_file(file_path, user_id)
            print(f"✅ [Worker 完成] 用户 {user_id} 专属知识库构建完毕！")
        except Exception as e:
            print(f"❌ [Worker 失败] 错误详情: {str(e)}")
async def main():
    """启动消费者持续监听"""
    if not RABBITMQ_URL:
        raise RuntimeError(
            "没有读取到 RABBITMQ_URL，请检查 .env 文件"
        )

    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    # 核心限流配置：每次最多只从队列拿 1 个任务，防止内存打满
    await channel.set_qos(prefetch_count=1)

    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    print(f"[*] 🚀 知识库解析 Worker 已启动，正在监听 '{QUEUE_NAME}' 队列。退出请按 CTRL+C")

    await queue.consume(process_message)
    await asyncio.Future()
if __name__ == "__main__":
    # 兼容 Windows 系统的底层异步事件循环机制
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
