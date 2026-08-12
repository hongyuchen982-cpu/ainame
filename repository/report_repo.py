from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.naming_report import NamingReport
from models.user import User


class NamingReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_request(
        self, request_id: str, user_id: int
    ) -> NamingReport | None:
        async with self.session.begin():
            return await self.session.scalar(
                select(NamingReport).where(
                    NamingReport.client_request_id == request_id,
                    NamingReport.user_id == user_id,
                )
            )

    async def create(self, **values) -> NamingReport:
        async with self.session.begin():
            item = NamingReport(**values)
            self.session.add(item)
            await self.session.flush()
            return item

    async def list_for_user(self, user_id: int) -> list[NamingReport]:
        async with self.session.begin():
            return list(
                await self.session.scalars(
                    select(NamingReport)
                    .where(NamingReport.user_id == user_id)
                    .order_by(NamingReport.id.desc())
                    .limit(100)
                )
            )

    async def get_for_user(self, report_id: int, user_id: int) -> NamingReport | None:
        async with self.session.begin():
            return await self.session.scalar(
                select(NamingReport).where(
                    NamingReport.id == report_id, NamingReport.user_id == user_id
                )
            )

    async def get_any(self, report_id: int) -> NamingReport | None:
        async with self.session.begin():
            return await self.session.get(NamingReport, report_id)

    async def list_all(self) -> list[tuple[NamingReport, User]]:
        async with self.session.begin():
            return list(
                (
                    await self.session.execute(
                        select(NamingReport, User)
                        .join(User, User.id == NamingReport.user_id)
                        .order_by(NamingReport.id.desc())
                        .limit(200)
                    )
                ).all()
            )
