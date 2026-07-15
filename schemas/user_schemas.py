from pydantic import BaseModel, Field, EmailStr, model_validator
from typing import Annotated, Literal, List

UsernameStr = Annotated[str, Field(..., min_length=4, max_length=20, 
description="用户名")]
RawPasswordStr = Annotated[str, Field(min_length=6, max_length=20, 
description="密码")]
class RegisterIn(BaseModel):
    email: EmailStr
    username: UsernameStr
    password: RawPasswordStr
    confirm_password: RawPasswordStr
    code: Annotated[str, Field(..., min_length=4, max_length=4)]
    # 字段全部校验完之后自动运行的验证方法
    @model_validator(mode="after")
    def password_is_match(self) -> "RegisterIn":
        password = self.password
        confirm_password = self.confirm_password
        if password != confirm_password:
            raise ValueError("密码不一致！")
        return self

class UserCreateSchema(BaseModel):
    email: EmailStr
    password: RawPasswordStr
    username: UsernameStr


class LoginIn(BaseModel):
    email:EmailStr
    password: RawPasswordStr
    
class UserSchema(BaseModel):
    id:Annotated[int,Field(...)]
    username: UsernameStr
    email: EmailStr  
    
class LoginOut(BaseModel):
    user: UserSchema
    access_token: str
    refresh_token: str