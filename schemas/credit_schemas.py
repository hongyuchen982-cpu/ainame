from pydantic import BaseModel
class CreditBalanceOut(BaseModel):
    balance: int