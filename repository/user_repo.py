from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from schemas.user_schemas import UserCreateSchema

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User|None:
        async with self.session.begin():
            return await self.session.scalar(select(User).filter(User.email==email))

    async def email_is_exist(self, email: str) -> bool:
        async with self.session.begin():
            stmt = select(exists().where(User.email==email))
            return await self.session.scalar(stmt)

    async def create(self, user_schema: UserCreateSchema) -> User:
        async with self.session.begin():
            user = User(**user_schema.model_dump())
            self.session.add(user)
            return user