from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from typing import Annotated

UsernameStr = Annotated[str, Field(..., min_length=4, max_length=20, 
description="用户名")]
RawPasswordStr = Annotated[str, Field(min_length=6, max_length=20, 
description="密码")]
class RegisterIn(BaseModel):
    email: EmailStr
    username: UsernameStr
    password: RawPasswordStr
    confirm_password: RawPasswordStr
    code: Annotated[str, Field(..., min_length=6, max_length=6, pattern="^[0-9]{6}$")]
    invite_code: str | None = Field(None, min_length=4, max_length=20, pattern="^[A-Za-z0-9]+$")
    @field_validator("invite_code", mode="before")
    @classmethod
    def normalize_invite_code(cls, value):
        return str(value).strip().upper() if value and str(value).strip() else None
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
    model_config = ConfigDict(from_attributes=True)

    id:Annotated[int,Field(...)]
    username: UsernameStr
    email: EmailStr
    avatar_url: str = ""
    status: str = "active"
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    
class LoginOut(BaseModel):
    user: UserSchema
    access_token: str
    refresh_token: str


class AccessTokenOut(BaseModel):
    access_token: str
    refresh_token: str


class TokenVerifyOut(BaseModel):
    message: str
    user_id: int


class ProfileUpdateIn(BaseModel):
    username: str | None = Field(None, min_length=4, max_length=20)
    avatar_url: str | None = Field(None, max_length=500)


class ChangePasswordIn(BaseModel):
    current_password: RawPasswordStr
    new_password: RawPasswordStr
    confirm_password: RawPasswordStr

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("两次新密码不一致")
        if self.current_password == self.new_password:
            raise ValueError("新密码不能与当前密码相同")
        return self


class PasswordResetCodeIn(BaseModel):
    email: EmailStr


class PasswordResetConfirmIn(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    new_password: RawPasswordStr
    confirm_password: RawPasswordStr

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("两次密码不一致")
        return self


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_name: str
    ip_address: str
    first_seen_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None


class LoginRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    ip_address: str
    user_agent: str
    success: bool
    failure_reason: str
    created_at: datetime


class DashboardReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    name: str
    file_size: int
    page_count: int
    created_at: datetime


class UserDashboardOut(BaseModel):
    credit_balance: int
    credit_total_used: int
    credit_total_recharge: int
    credit_logs: int
    projects_total: int
    projects_selected: int
    orders_total: int
    orders_pending: int
    knowledge_files: int
    knowledge_ready: int
    reports_total: int
    recent_reports: list[DashboardReportOut] = Field(default_factory=list)


class UserStatusIn(BaseModel):
    status: str = Field(..., pattern="^(active|frozen)$")


class UserRolesIn(BaseModel):
    roles: list[str] = Field(..., min_length=1)


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str
    is_system: bool
    permissions: list[str] = Field(default_factory=list)


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str


class RoleCreateIn(BaseModel):
    code: str = Field(..., min_length=2, max_length=50, pattern="^[a-z][a-z0-9_-]*$")
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field("", max_length=255)
    permissions: list[str] = Field(default_factory=list)


class RolePermissionsIn(BaseModel):
    permissions: list[str] = Field(default_factory=list)


class AdminUserOut(UserSchema):
    created_at: datetime


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    admin_user_id: int
    action: str
    target_type: str
    target_id: str
    detail: str
    ip_address: str
    created_at: datetime
