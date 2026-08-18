from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.brand_asset import BrandAsset
from models.user import User


class BrandAssetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_request(self, request_id: str, user_id: int) -> BrandAsset | None:
        async with self.session.begin():
            return await self.session.scalar(
                select(BrandAsset).where(
                    BrandAsset.client_request_id == request_id,
                    BrandAsset.user_id == user_id,
                )
            )

    async def create(self, **values) -> BrandAsset:
        async with self.session.begin():
            item = BrandAsset(**values)
            self.session.add(item)
            await self.session.flush()
            return item

    async def list_for_user(
        self, user_id: int, selected_name_id: int | None = None
    ) -> list[BrandAsset]:
        async with self.session.begin():
            statement = select(BrandAsset).where(BrandAsset.user_id == user_id)
            if selected_name_id is not None:
                statement = statement.where(
                    BrandAsset.selected_name_id == selected_name_id
                )
            return list(
                await self.session.scalars(
                    statement.order_by(BrandAsset.id.desc()).limit(100)
                )
            )

    async def get_for_user(self, asset_id: int, user_id: int) -> BrandAsset | None:
        async with self.session.begin():
            return await self.session.scalar(
                select(BrandAsset).where(
                    BrandAsset.id == asset_id,
                    BrandAsset.user_id == user_id,
                )
            )

    async def latest_for_project(
        self, project_id: int, user_id: int
    ) -> BrandAsset | None:
        async with self.session.begin():
            return await self.session.scalar(
                select(BrandAsset)
                .where(
                    BrandAsset.project_id == project_id, BrandAsset.user_id == user_id
                )
                .order_by(BrandAsset.id.desc())
                .limit(1)
            )

    async def list_all(self) -> list[tuple[BrandAsset, User]]:
        async with self.session.begin():
            return list(
                (
                    await self.session.execute(
                        select(BrandAsset, User)
                        .join(User, User.id == BrandAsset.user_id)
                        .order_by(BrandAsset.id.desc())
                        .limit(200)
                    )
                ).all()
            )
