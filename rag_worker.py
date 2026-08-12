import asyncio
import json
import os
import sys

import aio_pika
from dotenv import load_dotenv

from core.rag_service import delete_knowledge_file_vectors, process_and_store_file
from models import AsyncSessionFactory
from repository.knowledge_repo import KnowledgeRepository
from repository.task_repo import TaskRepository


load_dotenv()
RABBITMQ_URL = os.getenv("RABBITMQ_URL")
QUEUE_NAME = "rag_document_queue"


async def process_message(message: aio_pika.IncomingMessage):
    data = json.loads(message.body.decode("utf-8"))
    task_id = data.get("task_id")
    if not task_id:
        # Messages from the old untracked format cannot be updated safely.
        await message.ack()
        return

    async with AsyncSessionFactory() as session:
        task = await TaskRepository(session).claim(task_id)
    if task is None:
        async with AsyncSessionFactory() as session:
            current = await TaskRepository(session).get(task_id)
        if current is not None and current.status == "running":
            await asyncio.sleep(2)
            await message.reject(requeue=True)
        else:
            await message.ack()
        return

    payload = json.loads(task.payload)
    file_id = int(payload["file_id"])
    user_id = int(payload["user_id"])
    version = int(payload["version"])
    async with AsyncSessionFactory() as session:
        item = await KnowledgeRepository(session).claim_processing(
            file_id, version, allow_resume=task.attempt_count > 1
        )
    if item is None:
        async with AsyncSessionFactory() as session:
            await TaskRepository(session).cancel_stale(
                task_id, "关联文件已删除、已重试或状态发生变化"
            )
        await message.ack()
        return

    try:
        async with AsyncSessionFactory() as session:
            await TaskRepository(session).set_progress(task_id, 30)
        work = asyncio.create_task(asyncio.to_thread(
            process_and_store_file, item.storage_path, user_id, file_id, version
        ))
        while not work.done():
            try:
                await asyncio.wait_for(asyncio.shield(work), timeout=30)
            except TimeoutError:
                async with AsyncSessionFactory() as session:
                    await TaskRepository(session).heartbeat(task_id)
        chunk_count = await work
        async with AsyncSessionFactory() as session:
            await TaskRepository(session).set_progress(task_id, 90)
            accepted = await KnowledgeRepository(session).finish_processing(
                file_id, version, chunk_count
            )
        if not accepted:
            await asyncio.to_thread(
                delete_knowledge_file_vectors, user_id, file_id, version
            )
            async with AsyncSessionFactory() as session:
                await TaskRepository(session).cancel_stale(
                    task_id, "处理期间关联文件状态发生变化，结果已丢弃"
                )
        else:
            async with AsyncSessionFactory() as session:
                await TaskRepository(session).complete(
                    task_id, {"file_id": file_id, "chunk_count": chunk_count}
                )
        await message.ack()
    except Exception as exc:
        async with AsyncSessionFactory() as session:
            should_retry = await TaskRepository(session).fail_or_retry(task_id, str(exc))
            if should_retry:
                await KnowledgeRepository(session).schedule_retry(file_id, version, str(exc))
            else:
                await KnowledgeRepository(session).fail_processing(file_id, version, str(exc))
        if should_retry:
            await asyncio.sleep(min(2 ** task.attempt_count, 30))
            await message.reject(requeue=True)
        else:
            await message.ack()


async def main():
    if not RABBITMQ_URL:
        raise RuntimeError("没有读取到 RABBITMQ_URL，请检查 .env 文件")
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    print(f"Knowledge worker is listening on {QUEUE_NAME}")
    await queue.consume(process_message)
    await asyncio.Future()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
