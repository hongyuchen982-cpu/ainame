# core/mailtools.py
from fastapi_mail import FastMail, ConnectionConfig
from dotenv import load_dotenv
load_dotenv()
import os

def create_mail_instance() -> FastMail:

    """创建 FastMail 实例（每次调用返回新实例，线程/协程安全）"""
    mail_config = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=os.getenv("MAIL_PORT"),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS"),
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS"),
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    )
    
    return FastMail(mail_config)