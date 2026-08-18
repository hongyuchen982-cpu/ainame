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

    async def get_by_id(self, user_id: int) -> User | None:
        async with self.session.begin():
            return await self.session.get(User, user_id)

    async def email_is_exist(self, email: str) -> bool:
        async with self.session.begin():
            stmt = select(exists().where(User.email==email))
            return await self.session.scalar(stmt)

    async def create(self, user_schema: UserCreateSchema) -> User:
        async with self.session.begin():
            return await self.create_in_transaction(user_schema)

    async def create_in_transaction(self, user_schema: UserCreateSchema) -> User:
        """在调用方已经开启的事务中创建用户。"""
        user = User(**user_schema.model_dump())
        self.session.add(user)
        await self.session.flush()
        return user

    async def update_profile(self, user_id: int, *, username: str | None = None, avatar_url: str | None = None) -> User | None:
        async with self.session.begin():
            user = await self.session.get(User, user_id)
            if user is None:
                return None
            if username is not None:
                user.username = username
            if avatar_url is not None:
                user.avatar_url = avatar_url
            await self.session.flush()
            return user

    async def change_password(self, user_id: int, new_password: str) -> User | None:
        async with self.session.begin():
            user = await self.session.get(User, user_id)
            if user is None:
                return None
            user.password = new_password
            user.token_version += 1
            await self.session.flush()
            return user

    async def set_status(self, user_id: int, status: str) -> User | None:
        async with self.session.begin():
            return await self.set_status_in_transaction(user_id, status)

    async def set_status_in_transaction(self, user_id: int, status: str) -> User | None:
        user = await self.session.get(User, user_id)
        if user is None:
            return None
        user.status = status
        user.token_version += 1
        await self.session.flush()
        return user

    async def list_users(self, limit: int = 100, offset: int = 0) -> list[User]:
        async with self.session.begin():
            result = await self.session.scalars(
                select(User).order_by(User.id.desc()).offset(offset).limit(limit)
            )
            return list(result)
