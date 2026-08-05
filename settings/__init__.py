from datetime import timedelta
import os

JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=15)
JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=30)


DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "").strip().rstrip("/")
DASHSCOPE_IMAGE_API_URL = os.getenv(
    "DASHSCOPE_IMAGE_API_URL",
    (
        "https://dashscope.aliyuncs.com/api/v1/services/"
        "aigc/multimodal-generation/generation"
    ),
).strip()
WANXIANG_MODEL = os.getenv("WANXIANG_MODEL", "wan2.6-t2i")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000").strip().rstrip("/")
