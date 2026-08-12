from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from core.logo_tools import generate_company_logo
from dependencies import get_session
from repository.selected_name_repo import SelectedNameRepository
from schemas.logo_schemas import LogoGenerateIn, LogoGenerateOut

router = APIRouter(prefix="/logos", tags=["logos"])
auth_handler = AuthHandler()


@router.post("/generate", response_model=LogoGenerateOut)
async def generate_logo(
    data: LogoGenerateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repository = SelectedNameRepository(session)
    selected = await repository.get_for_user(data.selection_id, user_id)
    if selected is None:
        raise HTTPException(status_code=404, detail="最终名称不存在")
    if selected.category != "企业名":
        raise HTTPException(
            status_code=400,
            detail="只有已选定的企业名称可以生成 Logo",
        )

    # 图像接口和图片下载是同步 I/O，放在线程池中避免阻塞事件循环。
    logo = await run_in_threadpool(
        generate_company_logo,
        company_name=selected.name,
        style_feedback=data.style_feedback,
    )
    saved = await repository.save_logo_result(
        selection_id=selected.id,
        user_id=user_id,
        logo_prompt=logo["logo_prompt"],
        logo_url=logo["logo_url"],
        logo_status=logo["logo_status"],
    )
    if saved is None:
        raise HTTPException(status_code=404, detail="最终名称不存在")

    return {
        "selection_id": selected.id,
        "company_name": selected.name,
        **logo,
    }
