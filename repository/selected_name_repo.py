from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.selected_name import SelectedName


class SelectedNameRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def select_final_name(
        self,
        *,
        user_id: int,
        thread_id: str,
        category: str,
        candidate: dict,
        project_id: int | None = None,
    ) -> SelectedName:
        """每个命名 thread 只保留一个最终选择；重新选择时覆盖并清空旧 Logo。"""

        async with self.session.begin():
            return await self.select_final_name_in_transaction(
                user_id=user_id,
                thread_id=thread_id,
                category=category,
                candidate=candidate,
                project_id=project_id,
            )

    async def select_final_name_in_transaction(
        self,
        *,
        user_id: int,
        thread_id: str,
        category: str,
        candidate: dict,
        project_id: int | None = None,
    ) -> SelectedName:
        selected = await self.session.scalar(
            select(SelectedName)
            .where(SelectedName.thread_id == thread_id)
            .with_for_update()
        )

        if selected and selected.user_id != user_id:
            raise PermissionError("无权修改该命名会话")

        if selected is None:
            selected = SelectedName(
                user_id=user_id,
                thread_id=thread_id,
                project_id=project_id,
            )
            self.session.add(selected)
        elif project_id is not None:
            selected.project_id = project_id

        selected.category = category
        selected.name = candidate["name"]
        selected.reference = candidate.get("reference", "")
        selected.moral = candidate.get("moral", "")
        selected.logo_prompt = ""
        selected.logo_url = ""
        selected.logo_status = "not_generated"

        await self.session.flush()
        return selected

    async def get_for_user(
        self,
        selection_id: int,
        user_id: int,
    ) -> SelectedName | None:
        async with self.session.begin():
            return await self.session.scalar(
                select(SelectedName).where(
                    SelectedName.id == selection_id,
                    SelectedName.user_id == user_id,
                )
            )

    async def list_for_user(self, user_id: int) -> list[SelectedName]:
        async with self.session.begin():
            return list(await self.session.scalars(
                select(SelectedName)
                .where(SelectedName.user_id == user_id)
                .order_by(SelectedName.updated_at.desc())
                .limit(100)
            ))

    async def save_logo_result(
        self,
        *,
        selection_id: int,
        user_id: int,
        logo_prompt: str,
        logo_url: str,
        logo_status: str,
    ) -> SelectedName | None:
        async with self.session.begin():
            selected = await self.session.scalar(
                select(SelectedName)
                .where(
                    SelectedName.id == selection_id,
                    SelectedName.user_id == user_id,
                )
                .with_for_update()
            )
            if selected is None:
                return None

            selected.logo_prompt = logo_prompt
            selected.logo_url = logo_url
            selected.logo_status = logo_status
            await self.session.flush()
            return selected
