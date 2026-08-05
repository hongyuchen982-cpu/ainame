from contextlib import asynccontextmanager

from fastapi import FastAPI,Depends
from fastapi_mail import FastMail, MessageSchema, MessageType
from dependencies import get_email
from core.workflow import (
    start_naming_memory,
    stop_naming_memory,
)
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from routers.logo_router import router as logo_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_naming_memory()

    try:
        yield
    finally:
        await stop_naming_memory()


app = FastAPI(lifespan=lifespan)
BACKEND_DIR = Path(__file__).resolve().parent
STATIC_DIR = BACKEND_DIR / "static"
(STATIC_DIR / "logos").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/mail/test")
async def mail_test(email:str,mail:FastMail=Depends(get_email)):
#  1.准备邮件对象
    message = MessageSchema(
    subject="ainame验证码",
    recipients=[email],
    body=f"Hello {email}",  # 验证码是生产的
    subtype=MessageType.plain)
    await  mail.send_message(message)

    return {"message": "邮件发送成功！"}

from routers.auth_router import router as auth_router

app.include_router(auth_router)

from routers.name_router import router as name_router

app.include_router(name_router)

from routers.credit_router import router as credit_router
app.include_router(credit_router)


from routers.package_router import router as package_router
app.include_router(package_router)

from routers.pay_router import router as pay_router
app.include_router(pay_router)


from routers.rag_router import router as rag_router
app.include_router(rag_router)

app.include_router(logo_router)
