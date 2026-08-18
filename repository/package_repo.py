from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.package import Package
from models.user_order import UserOrder

class PackageRepository:

    def __init__(self,session:AsyncSession):

        self.session =session


    async def list_active(self) -> list[Package]:
        """
        查询所有上架套餐。
        """
        async with self.session.begin():

            result = await self.session.scalars(
            select(Package)
            .where(Package.is_active.is_(True))
            .order_by(Package.sort_order, Package.id)
                    )

            return list(result.all())
    async def get_by_id(self, package_id: int) -> Package | None:
        """
        根据套餐 id 查询套餐。
        """
        async with self.session.begin():
            return await self.session.scalar(
                select(Package).where(
                    Package.id == package_id,
                    Package.is_active.is_(True),
                        )
                    )

    async def list_all(self) -> list[Package]:
        async with self.session.begin():
            return list(await self.session.scalars(
                select(Package).order_by(Package.sort_order, Package.id)
            ))

    async def create_in_transaction(self, **values) -> Package:
        package = Package(**values)
        self.session.add(package)
        await self.session.flush()
        return package

    async def update_in_transaction(
        self, package_id: int, values: dict
    ) -> Package | None:
        package = await self.session.scalar(
            select(Package).where(Package.id == package_id).with_for_update()
        )
        if package is None:
            return None
        for key, value in values.items():
            setattr(package, key, value.strip() if isinstance(value, str) else value)
        await self.session.flush()
        return package

    async def set_status_in_transaction(
        self, package_id: int, is_active: bool
    ) -> Package | None:
        return await self.update_in_transaction(package_id, {"is_active": is_active})

    async def sort_in_transaction(self, items: list[dict]) -> list[Package]:
        ids = [item["id"] for item in items]
        packages = list(await self.session.scalars(
            select(Package).where(Package.id.in_(ids)).with_for_update()
        ))
        if len(packages) != len(ids):
            raise ValueError("部分套餐不存在")
        orders = {item["id"]: item["sort_order"] for item in items}
        for package in packages:
            package.sort_order = orders[package.id]
        await self.session.flush()
        return sorted(packages, key=lambda item: (item.sort_order, item.id))

    async def delete_in_transaction(self, package_id: int) -> bool:
        package = await self.session.scalar(
            select(Package).where(Package.id == package_id).with_for_update()
        )
        if package is None:
            return False
        order_count = await self.session.scalar(
            select(func.count()).select_from(UserOrder).where(UserOrder.package_id == package_id)
        )
        if order_count:
            raise ValueError("该套餐已有订单，不能删除，请改为下架")
        await self.session.delete(package)
        await self.session.flush()
        return True
