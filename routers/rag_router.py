import os
import shutil
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile

from core.authtools import AuthHandler
from core.rag_service import process_and_store_file

auth_handler = AuthHandler()
router = APIRouter(prefix="/knowledge", tags=["知识库"])

# 确保上传目录存在
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: int = Depends(auth_handler.auth_access_dependency),
):
    """用户上传专属参考文件（TXT/PDF）"""
    # 1. 拼接本地保存路径
    file_path = os.path.join(UPLOAD_DIR, f"{user_id}_{file.filename}")

    # 2. 将上传的文件写入本地磁盘
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. 将耗时的“文档切片+向量化”任务交给后台处理
    background_tasks.add_task(process_and_store_file, file_path, user_id)

    return {
        "result": "success",
        "message": (
            f"文件 {file.filename} 上传成功！"
            "后台正在为您构建专属知识库，请稍候测试起名功能。"
        ),
    }