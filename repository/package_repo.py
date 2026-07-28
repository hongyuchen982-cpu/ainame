from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.package import Package

class PackageRepository:

    def __init__(self,session:AsyncSession):

        self.session =session


    async def list_active(self) -> list[Package]:
        """
        查询所有上架套餐。
        """
        async with self.session.begin():

            result = await self.session.scalars(
            select(Package).where(Package.is_active == True)
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
                    Package.is_active == True,
                        )
                    )
