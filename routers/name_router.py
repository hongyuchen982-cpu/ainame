import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from core.workflow import generate_names_v2
from dependencies import get_session
from repository.credit_repo import CreditRepository
from schemas.name_schemas import NameIn, NameOut
from schemas.name_schemas import NameWithThreadOut
from core.workflow import generate_names_v2, feedback_names

auth_handler = AuthHandler()
router = APIRouter(prefix="/name")




@router.post(path="/generate", response_model=NameWithThreadOut)
async def take_names_first_time(
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
        # 2. 调用带记忆的智能体工作流
        output_data = await generate_names_v2(
            data,
            user_id
        )

        # 3. AI成功后扣除一次
        await credit_repo.consume_name_credit(
            user_id=user_id
        )

        # 4. 返回结果 + thread_id
        return NameWithThreadOut(
            thread_id=output_data["thread_id"],
            names=output_data["names"]
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

import traceback
from schemas.name_schemas import FeedbackIn
@router.post(path="/feedback", response_model=NameWithThreadOut)
async def take_names_feedback(data: FeedbackIn, user_id: int =
Depends(auth_handler.auth_access_dependency)):
    """带有 Thread_ID 的多轮微调"""
    try:
        result = await feedback_names(data, user_id)
        return NameWithThreadOut(thread_id=result["thread_id"],
    names=result["data"].get("names", []))
    except Exception:
        traceback.print_exc()
    raise HTTPException(status_code=500, detail="微调失败")
