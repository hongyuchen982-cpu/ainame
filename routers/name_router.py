from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.authtools import AuthHandler
from core.nametools import generate_names
from dependencies import get_session
from repository.credit_repo import CreditRepository
from schemas.name_schemas import NameIn, NameOut

auth_handler = AuthHandler()
router = APIRouter(prefix="/name")


@router.post(path="/get_names", response_model=NameOut)
async def take_names(
data: NameIn,
user_id: int = Depends(auth_handler.auth_access_dependency),
session: AsyncSession = Depends(get_session),
):
    credit_repo = CreditRepository(session=session)
    # 1. 起名前先检查剩余次数
    balance = await credit_repo.get_balance(user_id=user_id)
 
    if balance <= 0:
            raise HTTPException(
                status_code=400,
                detail="起名次数已用完，请充值后继续使用！",
            )
        # 2. 有次数才调用 AI 起名
    try:
            name_result = await generate_names(data)
    except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"AI起名失败:{str(e)}",
                )
        # 3. AI 成功生成后，再扣除 1 次
    try:
        await credit_repo.consume_name_credit(user_id=user_id)
    except ValueError as e:
        raise HTTPException(
                status_code=400,
                detail=str(e),
            )
        # 4. 返回起名结果
    return NameOut(names=name_result.names)



