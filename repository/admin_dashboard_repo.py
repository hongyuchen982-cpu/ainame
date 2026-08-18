from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.async_task import AsyncTask
from models.knowledge_file import KnowledgeFile
from models.naming_project import NamingProject
from models.naming_report import NamingReport
from models.selected_name import SelectedName
from models.user import User
from models.user_order import UserOrder


class AdminDashboardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _count(self, model, *conditions) -> int:
        value = await self.session.scalar(
            select(func.count()).select_from(model).where(*conditions)
        )
        return int(value or 0)

    async def summary(self) -> dict:
        async with self.session.begin():
            revenue = await self.session.scalar(
                select(func.coalesce(func.sum(UserOrder.amount), 0)).where(
                    UserOrder.status == "paid"
                )
            )
            return {
                "users_total": await self._count(User),
                "users_active": await self._count(User, User.status == "active"),
                "projects_total": await self._count(NamingProject),
                "projects_selected": await self._count(
                    NamingProject, NamingProject.status == "selected"
                ),
                "orders_total": await self._count(UserOrder),
                "orders_pending": await self._count(
                    UserOrder, UserOrder.status == "pending"
                ),
                "paid_revenue": Decimal(revenue or 0),
                "reports_total": await self._count(NamingReport),
                "knowledge_files": await self._count(
                    KnowledgeFile, KnowledgeFile.deleted_at.is_(None)
                ),
                "tasks_running": await self._count(
                    AsyncTask, AsyncTask.status.in_(["queued", "running"])
                ),
            }

    async def projects(
        self, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        async with self.session.begin():
            statement = (
                select(NamingProject, User, SelectedName.name)
                .join(User, User.id == NamingProject.user_id)
                .outerjoin(SelectedName, SelectedName.project_id == NamingProject.id)
                .order_by(NamingProject.updated_at.desc(), NamingProject.id.desc())
                .offset(offset)
                .limit(limit)
            )
            if status:
                statement = statement.where(NamingProject.status == status)
            rows = (await self.session.execute(statement)).all()
            return [
                {
                    "id": project.id,
                    "user_id": user.id,
                    "username": user.username,
                    "user_email": user.email,
                    "title": project.title,
                    "category": project.category,
                    "status": project.status,
                    "current_round": project.current_round,
                    "final_name": final_name,
                    "created_at": project.created_at,
                    "updated_at": project.updated_at,
                }
                for project, user, final_name in rows
            ]
