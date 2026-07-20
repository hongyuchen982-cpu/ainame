from fastapi import FastAPI,Depends
from fastapi_mail import FastMail, MessageSchema, MessageType
from dependencies import get_email


app = FastAPI()


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