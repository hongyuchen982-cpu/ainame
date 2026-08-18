from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
class CreateOrderIn(BaseModel):

    package_id: int = Field(..., ge=1)
    client_request_id: str | None = Field(None, min_length=8, max_length=100)

class CreateOrderOut(BaseModel):

    order_no: str
    amount: Decimal
    credit_count: int
    pay_url: str

class OrderStatusOut(BaseModel):

    order_no: str
    package_name: str
    amount: Decimal
    credit_count: int
    status: Literal["pending", "paid", "closed", "refunding", "refunded"]
    alipay_trade_no: str
    refund_amount: Decimal
    created_at: datetime
    paid_at: datetime | None
    closed_at: datetime | None
    refunded_at: datetime | None
    expires_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PaymentTransactionOut(BaseModel):
    id: int
    request_no: str
    transaction_type: str
    status: str
    amount: Decimal
    provider_trade_no: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderDetailOut(OrderStatusOut):
    transactions: list[PaymentTransactionOut]


class AdminOrderOut(OrderStatusOut):
    user_id: int
    email: str
    username: str


class AdminOrderDetailOut(AdminOrderOut):
    transactions: list[PaymentTransactionOut]


class RefundOrderIn(BaseModel):
    request_no: str = Field(..., min_length=8, max_length=100)
    reason: str = Field(..., min_length=2, max_length=200)
