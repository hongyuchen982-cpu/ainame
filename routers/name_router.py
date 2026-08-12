import traceback

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from core.distributed_lock import OperationBusyError, distributed_operation_lock
from core.workflow import (
    delete_naming_thread,
    feedback_names,
    generate_names_v2,
    get_naming_candidates,
    get_naming_state,
    restore_naming_state,
)
from core.redistools import get_redis
from dependencies import get_session
from repository.credit_repo import CreditRepository
from repository.project_repo import NamingProjectRepository
from repository.selected_name_repo import SelectedNameRepository
from schemas.name_schemas import (
    FeedbackIn,
    NameIn,
    NameSelectIn,
    NameWithThreadOut,
    SelectedNameOut,
)


auth_handler = AuthHandler()
router = APIRouter(prefix="/name")


@router.post(path="/generate", response_model=NameWithThreadOut)
async def take_names_first_time(
    data: NameIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    try:
        lock_key = (
            f"lock:naming:project:{data.project_id}"
            if data.project_id is not None
            else f"lock:naming:user:{user_id}:generate"
        )
        async with distributed_operation_lock(redis, lock_key):
            credit_repo = CreditRepository(session)
            project_repo = NamingProjectRepository(session)
            balance = await credit_repo.get_balance(user_id=user_id)
            if balance <= 0:
                raise HTTPException(status_code=400, detail="起名次数已用完，请充值后继续使用！")

            if data.project_id is not None:
                draft = await project_repo.get_for_user(data.project_id, user_id)
                if draft is None:
                    raise HTTPException(status_code=404, detail="命名项目不存在")
                if draft.status != "draft":
                    raise HTTPException(status_code=400, detail="只有草稿项目可以开始首次生成")

            output_data = await generate_names_v2(data, user_id)
            candidates = [
                item.model_dump() if hasattr(item, "model_dump") else dict(item)
                for item in output_data["names"]
            ]
            conditions = data.model_dump(exclude={"project_id"})

            try:
                # 项目候选快照与次数扣减必须同时成功或同时回滚。
                async with session.begin():
                    project = await project_repo.create_generated_in_transaction(
                        user_id=user_id,
                        project_id=data.project_id,
                        thread_id=output_data["thread_id"],
                        category=data.category,
                        conditions=conditions,
                        candidates=candidates,
                    )
                    await credit_repo.consume_name_credit_in_transaction(
                        user_id,
                        operation_id=f"name:{output_data['thread_id']}",
                    )
            except Exception:
                await delete_naming_thread(output_data["thread_id"])
                raise

            return NameWithThreadOut(
                thread_id=output_data["thread_id"],
                project_id=project.id,
                names=output_data["names"],
            )
    except OperationBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"智能体执行失败，请检查终端日志。内部错误信息: {str(exc)}",
        ) from exc


@router.post(path="/feedback", response_model=NameWithThreadOut)
async def take_names_feedback(
    data: FeedbackIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
):
    """带有 Thread_ID 的多轮微调，并保存项目轮次历史。"""
    try:
        async with distributed_operation_lock(
            redis, f"lock:naming:thread:{data.thread_id}"
        ):
            project_repo = NamingProjectRepository(session)
            project = await project_repo.get_by_thread(data.thread_id, user_id)
            if project is None:
                raise LookupError("命名项目不存在")
            if project.status == "archived":
                raise PermissionError("归档项目不能继续修改")
            if project.category != data.category:
                raise ValueError("反馈类型与命名项目不一致")

            previous_state = await get_naming_state(data.thread_id, user_id)
            result = await feedback_names(data, user_id)
            candidates = result["data"].get("names", [])
            try:
                project = await project_repo.append_round(
                    user_id=user_id,
                    thread_id=data.thread_id,
                    feedback=data.feedback,
                    candidates=candidates,
                )
            except Exception:
                await restore_naming_state(data.thread_id, user_id, previous_state)
                raise
            return NameWithThreadOut(
                thread_id=result["thread_id"],
                project_id=project.id,
                names=candidates,
            )
    except OperationBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="微调失败") from exc


def selected_name_response(selected) -> dict:
    return {
        "id": selected.id,
        "project_id": selected.project_id,
        "thread_id": selected.thread_id,
        "category": selected.category,
        "name": selected.name,
        "reference": selected.reference,
        "moral": selected.moral,
        "logo_prompt": selected.logo_prompt,
        "logo_url": selected.logo_url,
        "logo_status": selected.logo_status,
        "can_generate_logo": selected.category == "企业名",
    }


@router.post(path="/select", response_model=SelectedNameOut)
async def select_final_name(
    data: NameSelectIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    """从当前会话最新生成的候选名中确认一个最终名称。"""
    try:
        project_repo = NamingProjectRepository(session)
        project = await project_repo.get_by_thread(data.thread_id, user_id)
        stored = (
            await project_repo.latest_candidates(project.id, user_id)
            if project is not None else None
        )
        if stored is not None:
            category, candidates = stored
        else:
            category, candidates = await get_naming_candidates(
                thread_id=data.thread_id,
                user_id=user_id,
            )
        candidate = next(
            (item for item in candidates if item.get("name") == data.name),
            None,
        )
        if candidate is None:
            raise HTTPException(
                status_code=400,
                detail="所选名称不在该会话的最新候选列表中",
            )

        async with session.begin():
            # 兼容迁移前已经存在于 LangGraph 中的历史会话。
            if project is None:
                project = await project_repo.create_generated_in_transaction(
                    user_id=user_id,
                    thread_id=data.thread_id,
                    category=category,
                    conditions={"category": category},
                    candidates=candidates,
                )
            selected = await SelectedNameRepository(session).select_final_name_in_transaction(
                user_id=user_id,
                thread_id=data.thread_id,
                category=category,
                candidate=candidate,
                project_id=project.id,
            )
            await project_repo.mark_selected_in_transaction(project.id)
        return selected_name_response(selected)
    except HTTPException:
        raise
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(path="/selections/{selection_id}", response_model=SelectedNameOut)
async def get_selected_name(
    selection_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    selected = await SelectedNameRepository(session).get_for_user(selection_id, user_id)
    if selected is None:
        raise HTTPException(status_code=404, detail="最终名称不存在")
    return selected_name_response(selected)


@router.get(path="/selections", response_model=list[SelectedNameOut])
async def list_selected_names(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    items = await SelectedNameRepository(session).list_for_user(user_id)
    return [selected_name_response(item) for item in items]
