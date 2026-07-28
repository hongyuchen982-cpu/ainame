import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from core.workflow import generate_names_v2
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

    # 1. 起名前检查剩余次数
    balance = await credit_repo.get_balance(user_id=user_id)

    if balance <= 0:
        raise HTTPException(
            status_code=400,
            detail="起名次数已用完，请充值后继续使用！",
        )

    try:
        # 2. 调用新的多智能体工作流
        output_data = await generate_names_v2(data,user_id)

        # 3. AI成功后扣除一次
        await credit_repo.consume_name_credit(user_id=user_id)

        # 4. 返回结果
        return NameOut(
            names=output_data.get("names", [])
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"智能体执行失败，请检查终端日志。内部错误信息: {str(e)}",
        )