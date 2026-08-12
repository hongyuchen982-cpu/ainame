from contextlib import asynccontextmanager

from fastapi import FastAPI
from core.workflow import (
    start_naming_memory,
    stop_naming_memory,
)
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from routers.logo_router import router as logo_router
from routers.user_router import router as user_router
from routers.admin_router import router as admin_router
from routers.project_router import router as project_router
from routers.task_router import admin_router as admin_task_router, router as task_router
from routers.validation_router import admin_router as admin_validation_router, router as validation_router
from routers.brand_asset_router import admin_router as admin_brand_asset_router, router as brand_asset_router
from routers.report_router import admin_router as admin_report_router, router as report_router
from routers.expert_router import admin_router as admin_expert_router, expert_router, router as expert_public_router
from routers.community_router import admin_router as admin_community_router, router as community_router
from routers.developer_router import admin_router as admin_developer_router, api_router as open_api_router, router as developer_router
from routers.growth_router import admin_router as admin_growth_router, router as growth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_naming_memory()

    try:
        yield
    finally:
        await stop_naming_memory()


app = FastAPI(lifespan=lifespan)
BACKEND_DIR = Path(__file__).resolve().parent
STATIC_DIR = BACKEND_DIR / "static"
(STATIC_DIR / "logos").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

from routers.auth_router import router as auth_router

app.include_router(auth_router)

from routers.name_router import router as name_router

app.include_router(name_router)

from routers.credit_router import router as credit_router
app.include_router(credit_router)


from routers.package_router import admin_router as admin_package_router, router as package_router
app.include_router(package_router)
app.include_router(admin_package_router)

from routers.pay_router import admin_router as admin_order_router, router as pay_router
app.include_router(pay_router)
app.include_router(admin_order_router)


from routers.rag_router import admin_router as admin_knowledge_router, router as rag_router
app.include_router(rag_router)
app.include_router(admin_knowledge_router)
app.include_router(task_router)
app.include_router(admin_task_router)
app.include_router(validation_router)
app.include_router(admin_validation_router)
app.include_router(brand_asset_router)
app.include_router(admin_brand_asset_router)
app.include_router(report_router)
app.include_router(admin_report_router)
app.include_router(expert_public_router)
app.include_router(expert_router)
app.include_router(admin_expert_router)
app.include_router(community_router)
app.include_router(admin_community_router)
app.include_router(developer_router)
app.include_router(open_api_router)
app.include_router(admin_developer_router)
app.include_router(growth_router)
app.include_router(admin_growth_router)

app.include_router(logo_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(project_router)
