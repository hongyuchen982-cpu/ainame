from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from core.authtools import AuthHandler
from dependencies import get_session
from repository.credit_repo import CreditRepository
from schemas.credit_schemas import CreditAccountOut, CreditBalanceOut, CreditLogOut

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


@router.get("/account", response_model=CreditAccountOut)
async def get_credit_account(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    account = await CreditRepository(session).get_account(user_id)
    if account is None:
        raise HTTPException(status_code=404, detail="次数账户不存在")
    return account


@router.get("/logs", response_model=list[CreditLogOut])
async def list_credit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await CreditRepository(session).list_logs(
        user_id, limit=limit, offset=offset
    )
