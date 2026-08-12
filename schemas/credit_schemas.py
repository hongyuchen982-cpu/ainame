from datetime import datetime

from pydantic import BaseModel, Field


class CreditBalanceOut(BaseModel):
    balance: int


class CreditAccountOut(BaseModel):
    balance: int
    total_used: int
    total_recharge: int


class CreditLogOut(BaseModel):
    id: int
    change_count: int
    balance_after: int
    type: str
    remark: str
    operation_id: str | None
    created_at: datetime


class AdminCreditAccountOut(CreditAccountOut):
    user_id: int
    email: str
    username: str


class AdminCreditAdjustIn(BaseModel):
    change_count: int = Field(..., ge=-100000, le=100000)
    remark: str = Field(..., min_length=2, max_length=200)
    operation_id: str = Field(..., min_length=8, max_length=100)
