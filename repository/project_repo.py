from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.naming_project import NamingCandidate, NamingProject, NamingRound
from models.selected_name import SelectedName


class NamingProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def default_title(category: str, conditions: dict[str, Any]) -> str:
        subject = str(conditions.get("surname") or conditions.get("other") or "").strip()
        if subject:
            return f"{category} · {subject[:24]}"
        return f"{category}命名项目"

    async def create_draft(
        self,
        *,
        user_id: int,
        title: str,
        category: str,
        conditions: dict[str, Any],
    ) -> NamingProject:
        async with self.session.begin():
            project = NamingProject(
                user_id=user_id,
                title=title.strip(),
                category=category,
                status="draft",
                conditions=conditions,
            )
            self.session.add(project)
            await self.session.flush()
            return project

    async def get_for_user(self, project_id: int, user_id: int) -> NamingProject | None:
        async with self.session.begin():
            return await self.session.scalar(
                select(NamingProject).where(
                    NamingProject.id == project_id,
                    NamingProject.user_id == user_id,
                )
            )

    async def get_by_thread(self, thread_id: str, user_id: int) -> NamingProject | None:
        async with self.session.begin():
            return await self.session.scalar(
                select(NamingProject).where(
                    NamingProject.thread_id == thread_id,
                    NamingProject.user_id == user_id,
                )
            )

    async def latest_candidates(
        self, project_id: int, user_id: int
    ) -> tuple[str, list[dict[str, Any]]] | None:
        async with self.session.begin():
            project = await self.session.scalar(
                select(NamingProject).where(
                    NamingProject.id == project_id,
                    NamingProject.user_id == user_id,
                )
            )
            if project is None or project.current_round <= 0:
                return None
            naming_round = await self.session.scalar(
                select(NamingRound).where(
                    NamingRound.project_id == project.id,
                    NamingRound.round_no == project.current_round,
                )
            )
            if naming_round is None:
                return None
            candidates = list(await self.session.scalars(
                select(NamingCandidate)
                .where(NamingCandidate.round_id == naming_round.id)
                .order_by(NamingCandidate.id)
            ))
            return project.category, [
                {
                    "name": item.name,
                    "reference": item.reference,
                    "moral": item.moral,
                    "domain": item.domain,
                    "domain_status": item.domain_status,
                }
                for item in candidates
            ]

    async def list_for_user(
        self,
        user_id: int,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[NamingProject, str | None]]:
        async with self.session.begin():
            statement = (
                select(NamingProject, SelectedName.name)
                .outerjoin(SelectedName, SelectedName.project_id == NamingProject.id)
                .where(NamingProject.user_id == user_id)
                .order_by(NamingProject.updated_at.desc(), NamingProject.id.desc())
                .offset(offset)
                .limit(limit)
            )
            if status:
                statement = statement.where(NamingProject.status == status)
            return list((await self.session.execute(statement)).all())

    async def create_generated_in_transaction(
        self,
        *,
        user_id: int,
        thread_id: str,
        category: str,
        conditions: dict[str, Any],
        candidates: list[dict[str, Any]],
        project_id: int | None = None,
    ) -> NamingProject:
        if project_id is not None:
            project = await self.session.scalar(
                select(NamingProject)
                .where(
                    NamingProject.id == project_id,
                    NamingProject.user_id == user_id,
                )
                .with_for_update()
            )
            if project is None:
                raise ValueError("命名项目不存在")
            if project.status == "archived":
                raise ValueError("归档项目不能继续生成")
            if project.current_round > 0 or project.thread_id:
                raise ValueError("该项目已经生成过候选名称")
        else:
            project = NamingProject(
                user_id=user_id,
                title=self.default_title(category, conditions),
                category=category,
                conditions=conditions,
            )
            self.session.add(project)
            await self.session.flush()

        project.category = category
        project.conditions = conditions
        project.thread_id = thread_id
        project.status = "generated"
        project.current_round = 1
        project.archived_at = None
        await self._add_round(project.id, 1, "", candidates)
        await self.session.flush()
        return project

    async def append_round(
        self,
        *,
        user_id: int,
        thread_id: str,
        feedback: str,
        candidates: list[dict[str, Any]],
    ) -> NamingProject:
        async with self.session.begin():
            project = await self.session.scalar(
                select(NamingProject)
                .where(
                    NamingProject.thread_id == thread_id,
                    NamingProject.user_id == user_id,
                )
                .with_for_update()
            )
            if project is None:
                raise ValueError("命名项目不存在")
            if project.status == "archived":
                raise PermissionError("归档项目不能继续修改")
            next_round = project.current_round + 1
            await self._add_round(project.id, next_round, feedback, candidates)
            project.current_round = next_round
            if project.status != "selected":
                project.status = "generated"
            await self.session.flush()
            return project

    async def _add_round(
        self,
        project_id: int,
        round_no: int,
        feedback: str,
        candidates: list[dict[str, Any]],
    ) -> NamingRound:
        naming_round = NamingRound(
            project_id=project_id,
            round_no=round_no,
            feedback=feedback.strip(),
        )
        self.session.add(naming_round)
        await self.session.flush()
        candidate_rows = []
        for item in candidates:
            values = item.model_dump() if hasattr(item, "model_dump") else item
            candidate_rows.append(NamingCandidate(
                round_id=naming_round.id,
                name=str(values.get("name", "")),
                reference=str(values.get("reference", "")),
                moral=str(values.get("moral", "")),
                domain=str(values.get("domain", "")),
                domain_status=str(values.get("domain_status", "")),
            ))
        self.session.add_all(candidate_rows)
        return naming_round

    async def detail_parts(
        self, project_id: int, user_id: int
    ) -> tuple[NamingProject | None, list[tuple[NamingRound, list[NamingCandidate]]], SelectedName | None]:
        async with self.session.begin():
            project = await self.session.scalar(
                select(NamingProject).where(
                    NamingProject.id == project_id,
                    NamingProject.user_id == user_id,
                )
            )
            if project is None:
                return None, [], None
            rounds = list(await self.session.scalars(
                select(NamingRound)
                .where(NamingRound.project_id == project.id)
                .order_by(NamingRound.round_no)
            ))
            candidates_by_round: dict[int, list[NamingCandidate]] = {
                item.id: [] for item in rounds
            }
            if rounds:
                all_candidates = list(await self.session.scalars(
                    select(NamingCandidate)
                    .where(NamingCandidate.round_id.in_([item.id for item in rounds]))
                    .order_by(NamingCandidate.round_id, NamingCandidate.id)
                ))
                for candidate in all_candidates:
                    candidates_by_round[candidate.round_id].append(candidate)
            round_items = [
                (item, candidates_by_round[item.id]) for item in rounds
            ]
            selected = await self.session.scalar(
                select(SelectedName).where(SelectedName.project_id == project.id)
            )
            return project, round_items, selected

    async def update_project(
        self,
        project_id: int,
        user_id: int,
        *,
        title: str | None = None,
        conditions: dict[str, Any] | None = None,
    ) -> NamingProject | None:
        async with self.session.begin():
            project = await self.session.scalar(
                select(NamingProject).where(
                    NamingProject.id == project_id,
                    NamingProject.user_id == user_id,
                )
            )
            if project is None:
                return None
            if title is not None:
                project.title = title.strip()
            if conditions is not None:
                if project.status != "draft":
                    raise ValueError("只有草稿项目可以修改命名条件")
                project.conditions = conditions
                project.category = str(conditions["category"])
            await self.session.flush()
            return project

    async def set_archived(
        self, project_id: int, user_id: int, archived: bool
    ) -> NamingProject | None:
        async with self.session.begin():
            project = await self.session.scalar(
                select(NamingProject)
                .where(
                    NamingProject.id == project_id,
                    NamingProject.user_id == user_id,
                )
                .with_for_update()
            )
            if project is None:
                return None
            if archived:
                project.status = "archived"
                project.archived_at = datetime.now()
            else:
                selected_id = await self.session.scalar(
                    select(SelectedName.id).where(SelectedName.project_id == project.id)
                )
                project.status = (
                    "selected" if selected_id else "generated" if project.current_round else "draft"
                )
                project.archived_at = None
            await self.session.flush()
            return project

    async def mark_selected_in_transaction(self, project_id: int) -> None:
        project = await self.session.scalar(
            select(NamingProject).where(NamingProject.id == project_id).with_for_update()
        )
        if project is None:
            raise ValueError("命名项目不存在")
        if project.status == "archived":
            raise PermissionError("归档项目不能选择最终名称")
        project.status = "selected"
        await self.session.flush()
