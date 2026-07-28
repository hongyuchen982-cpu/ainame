from decimal import Decimal
from pydantic import BaseModel, ConfigDict
class CreateOrderIn(BaseModel):

    package_id: int

class CreateOrderOut(BaseModel):

    order_no: str
    amount: Decimal
    credit_count: int
    pay_url: str

class OrderStatusOut(BaseModel):

    order_no: str
    amount: Decimal
    credit_count: int
    status: str

    model_config = ConfigDict(from_attributes=True)
