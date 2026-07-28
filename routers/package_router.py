from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_session
from repository.package_repo import PackageRepository
from schemas.package_schemas import PackageOut


router = APIRouter(prefix="/package")
@router.get("/list", response_model=list[PackageOut])


async def package_list(
    session: AsyncSession = Depends(get_session),
):
    package_repo = PackageRepository(session=session)
    packages = await package_repo.list_active()
    return packages