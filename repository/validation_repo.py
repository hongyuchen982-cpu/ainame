from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.name_validation import NameValidation
from models.user import User


class NameValidationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_request(self, request_id: str, user_id: int) -> NameValidation | None:
        async with self.session.begin():
            return await self.session.scalar(select(NameValidation).where(
                NameValidation.client_request_id == request_id,
                NameValidation.user_id == user_id,
            ))

    async def create(self, **values) -> NameValidation:
        async with self.session.begin():
            item = NameValidation(**values)
            self.session.add(item)
            await self.session.flush()
            return item

    async def list_for_user(
        self, user_id: int, selected_name_id: int | None = None
    ) -> list[NameValidation]:
        async with self.session.begin():
            statement = select(NameValidation).where(NameValidation.user_id == user_id)
            if selected_name_id is not None:
                statement = statement.where(NameValidation.selected_name_id == selected_name_id)
            return list(await self.session.scalars(
                statement.order_by(NameValidation.id.desc()).limit(100)
            ))

    async def get_for_user(self, validation_id: int, user_id: int) -> NameValidation | None:
        async with self.session.begin():
            return await self.session.scalar(select(NameValidation).where(
                NameValidation.id == validation_id,
                NameValidation.user_id == user_id,
            ))

    async def latest_for_selection(
        self, selected_name_id: int, user_id: int
    ) -> NameValidation | None:
        async with self.session.begin():
            return await self.session.scalar(
                select(NameValidation)
                .where(
                    NameValidation.selected_name_id == selected_name_id,
                    NameValidation.user_id == user_id,
                )
                .order_by(NameValidation.id.desc())
                .limit(1)
            )

    async def list_all(
        self, risk_level: str | None = None, status: str | None = None
    ) -> list[tuple[NameValidation, User]]:
        async with self.session.begin():
            statement = select(NameValidation, User).join(User, User.id == NameValidation.user_id)
            if risk_level:
                statement = statement.where(NameValidation.risk_level == risk_level)
            if status:
                statement = statement.where(NameValidation.status == status)
            return list((await self.session.execute(
                statement.order_by(NameValidation.id.desc()).limit(200)
            )).all())
