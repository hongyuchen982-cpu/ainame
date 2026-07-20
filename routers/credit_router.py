from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.authtools import AuthHandler
from dependencies import get_session
from repository.credit_repo import CreditRepository
from schemas.credit_schemas import CreditBalanceOut

router = APIRouter(prefix="/credit")
auth_handler = AuthHandler()

@router.get("/balance", response_model=CreditBalanceOut)
async def get_credit_balance(
user_id: int = Depends(auth_handler.auth_access_dependency),
session: AsyncSession = Depends(get_session),
):
    credit_repo = CreditRepository(session=session)
    balance = await credit_repo.get_balance(user_id=user_id)
    return CreditBalanceOut(balance=balance)