from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.knowledge_file import KnowledgeFile
from models.naming_project import NamingProject
from models.naming_report import NamingReport
from models.user_credit import CreditLog, UserCredit
from models.user_order import UserOrder


class UserDashboardRepository:
    """Read-only aggregation for the authenticated user's workspace."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _count(self, model, *conditions) -> int:
        value = await self.session.scalar(
            select(func.count()).select_from(model).where(*conditions)
        )
        return int(value or 0)

    async def get(self, user_id: int) -> dict:
        async with self.session.begin():
            credit = await self.session.scalar(
                select(UserCredit).where(UserCredit.user_id == user_id)
            )
            projects_total = await self._count(
                NamingProject, NamingProject.user_id == user_id
            )
            projects_selected = await self._count(
                NamingProject,
                NamingProject.user_id == user_id,
                NamingProject.status == "selected",
            )
            credit_logs = await self._count(CreditLog, CreditLog.user_id == user_id)
            orders_total = await self._count(UserOrder, UserOrder.user_id == user_id)
            orders_pending = await self._count(
                UserOrder,
                UserOrder.user_id == user_id,
                UserOrder.status == "pending",
            )
            knowledge_files = await self._count(
                KnowledgeFile,
                KnowledgeFile.user_id == user_id,
                KnowledgeFile.deleted_at.is_(None),
            )
            knowledge_ready = await self._count(
                KnowledgeFile,
                KnowledgeFile.user_id == user_id,
                KnowledgeFile.deleted_at.is_(None),
                KnowledgeFile.status == "completed",
            )
            reports_total = await self._count(
                NamingReport, NamingReport.user_id == user_id
            )
            recent_reports = list(
                await self.session.scalars(
                    select(NamingReport)
                    .where(NamingReport.user_id == user_id)
                    .order_by(NamingReport.id.desc())
                    .limit(3)
                )
            )
            return {
                "credit_balance": credit.balance if credit else 0,
                "credit_total_used": credit.total_used if credit else 0,
                "credit_total_recharge": credit.total_recharge if credit else 0,
                "credit_logs": credit_logs,
                "projects_total": projects_total,
                "projects_selected": projects_selected,
                "orders_total": orders_total,
                "orders_pending": orders_pending,
                "knowledge_files": knowledge_files,
                "knowledge_ready": knowledge_ready,
                "reports_total": reports_total,
                "recent_reports": recent_reports,
            }
