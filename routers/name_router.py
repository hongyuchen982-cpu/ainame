from fastapi import APIRouter,Depends

from routers.auth_router import auth_handler
from schemas.name_schemas import NameIn, NameOut
from core.nametools import generate_names

from core.authtools import AuthHandler

auth_handler = AuthHandler()
router = APIRouter(prefix="/name")


@router.post(path="/get_names", response_model=NameOut)
async def take_names(
        data: NameIn,
    	# 校验token
        user_id: int = Depends(auth_handler.auth_access_dependency)
):
    name_result = await generate_names(data)
    return NameOut(names=name_result.names)