import json
import os
import shutil

import aio_pika
from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile

from core.authtools import AuthHandler
from core.rag_service import process_and_store_file

auth_handler = AuthHandler()
router = APIRouter(prefix="/knowledge", tags=["知识库"])

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# RabbitMQ 连接配置 协议://用户名:密码@主机地址:端口号
load_dotenv()

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
QUEUE_NAME = "rag_document_queue"


async def send_to_queue(message_dict: dict):
    """异步将任务发送到 RabbitMQ 队列"""
    if not RABBITMQ_URL:
        raise RuntimeError(
            "没有读取到 RABBITMQ_URL，请检查 .env 文件"
        )

    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        # 声明队列：durable=True 开启持久化，服务器重启任务不丢失
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)

        # 将任务字典转为 JSON 字节流发送
        message_body = json.dumps(message_dict).encode("utf-8")
        # 调用默认交换机，把封装好的消息发布出去
        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body),
            # 路由键只要和队列名字一模一样
            routing_key=queue.name,
        )


@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: int = Depends(auth_handler.auth_access_dependency),
):
    """
    用户上传专属参考文件（TXT/PDF）
    """
    # 第一步：完成文件在服务器的保存
    file_path = os.path.join(UPLOAD_DIR, f"{user_id}_{file.filename}")
    # 注意这里转换成绝对路径
    absolute_path = os.path.abspath(file_path)

    with open(absolute_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 第二步：构造任务包裹并投递到 RabbitMQ
    task_message = {"user_id": user_id, "file_path": absolute_path}
    await send_to_queue(task_message)

    return {
        "result": "success",
        "message": f"文件 {file.filename} 上传成功！后台正在为您构建专属知识库，请稍候测试起名功能。",
    }
