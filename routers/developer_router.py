import json
import time

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from core.workflow import delete_naming_thread, generate_names_v2
from dependencies import get_session
from repository.developer_repo import DeveloperRepository
from repository.security_repo import SecurityRepository
from routers.admin_router import request_ip
from schemas.developer_schemas import *
from schemas.name_schemas import NameIn


router = APIRouter(prefix="/developers", tags=["开放平台"])
api_router = APIRouter(prefix="/openapi/v1", tags=["开放 API"])
admin_router = APIRouter(prefix="/admin/developers", tags=["运营后台·开放平台"])
auth = AuthHandler()


def account_out(x): return {k:getattr(x,k) for k in ("id","company_name","contact_name","use_case","status","created_at")}
def key_out(x): return {k:getattr(x,k) for k in ("id","name","key_prefix","status","created_at","last_used_at","revoked_at")}
def plan_out(x): return {k:getattr(x,k) for k in ("id","name","description","price","quota_calls","validity_days","is_active","created_at")}
def sub_out(x,p): return {"id":x.id,"plan_id":p.id,"plan_name":p.name,"quota_total":x.quota_total,"quota_used":x.quota_used,"quota_remaining":max(0,x.quota_total-x.quota_used),"status":x.status,"starts_at":x.starts_at,"expires_at":x.expires_at}

@router.post("/account", response_model=DeveloperOut)
async def create_account(data:DeveloperCreateIn,user_id:int=Depends(auth.auth_access_dependency),session:AsyncSession=Depends(get_session)):
    try:return account_out(await DeveloperRepository(session).create_account(user_id,**data.model_dump()))
    except ValueError as e:raise HTTPException(400,str(e))

@router.get("/account",response_model=DeveloperOut|None)
async def account(user_id:int=Depends(auth.auth_access_dependency),session:AsyncSession=Depends(get_session)):
    x=await DeveloperRepository(session).account(user_id);return account_out(x) if x else None

@router.get("/keys",response_model=list[ApiKeyOut])
async def keys(user_id:int=Depends(auth.auth_access_dependency),session:AsyncSession=Depends(get_session)):
    try:return [key_out(x) for x in await DeveloperRepository(session).keys(user_id)]
    except LookupError as e:raise HTTPException(404,str(e))

@router.post("/keys",response_model=ApiKeyCreatedOut)
async def create_key(data:ApiKeyCreateIn,user_id:int=Depends(auth.auth_access_dependency),session:AsyncSession=Depends(get_session)):
    try:x,raw=await DeveloperRepository(session).create_key(user_id,data.name);return {**key_out(x),"api_key":raw}
    except LookupError as e:raise HTTPException(404,str(e))
    except ValueError as e:raise HTTPException(400,str(e))

@router.delete("/keys/{key_id}",response_model=ApiKeyOut)
async def revoke(key_id:int,user_id:int=Depends(auth.auth_access_dependency),session:AsyncSession=Depends(get_session)):
    try:return key_out(await DeveloperRepository(session).revoke_key(user_id,key_id))
    except LookupError as e:raise HTTPException(404,str(e))

@router.get("/plans",response_model=list[ApiPlanOut])
async def plans(session:AsyncSession=Depends(get_session)):return [plan_out(x) for x in await DeveloperRepository(session).plans()]

@router.post("/plans/{plan_id}/subscribe",response_model=ApiSubscriptionOut)
async def subscribe(plan_id:int,user_id:int=Depends(auth.auth_access_dependency),session:AsyncSession=Depends(get_session)):
    repo=DeveloperRepository(session)
    try:x=await repo.subscribe_free(user_id,plan_id);rows=await repo.subscriptions(x.developer_id);return sub_out(*next(r for r in rows if r[0].id==x.id))
    except LookupError as e:raise HTTPException(404,str(e))
    except ValueError as e:raise HTTPException(400,str(e))

@router.get("/subscriptions",response_model=list[ApiSubscriptionOut])
async def subscriptions(user_id:int=Depends(auth.auth_access_dependency),session:AsyncSession=Depends(get_session)):
    repo=DeveloperRepository(session);dev=await repo.account(user_id)
    if not dev:return []
    return [sub_out(*r) for r in await repo.subscriptions(dev.id)]

@router.get("/usage",response_model=list[ApiUsageOut])
async def usage(user_id:int=Depends(auth.auth_access_dependency),session:AsyncSession=Depends(get_session)):
    repo=DeveloperRepository(session);dev=await repo.account(user_id)
    if not dev:return []
    return [{k:getattr(x,k) for k in ("id","request_id","endpoint","units","status","error_message","latency_ms","created_at")} for x in await repo.usage(dev.id)]

@router.get("/usage/summary",response_model=ApiUsageSummaryOut)
async def usage_summary(user_id:int=Depends(auth.auth_access_dependency),session:AsyncSession=Depends(get_session)):
    repo=DeveloperRepository(session);dev=await repo.account(user_id)
    return {"calls_total":0,"units_total":0,"success_total":0,"failed_total":0} if not dev else await repo.usage_summary(dev.id)

async def api_identity(x_api_key:str=Header(...,alias="X-API-Key"),session:AsyncSession=Depends(get_session)):
    row=await DeveloperRepository(session).authenticate_key(x_api_key)
    if not row:raise HTTPException(401,"API Key 无效或已停用")
    return row

async def execute(data,request_id,endpoint,identity,session,batch=False):
    key,dev,_=identity;repo=DeveloperRepository(session);units=len(data) if batch else 1
    try:log,new=await repo.reserve(key.id,dev.id,request_id,endpoint,units)
    except ValueError as e:raise HTTPException(402,str(e))
    except LookupError as e:raise HTTPException(409,str(e))
    if not new:
        if log.status=="success":return log.response_data
        if log.status=="processing":raise HTTPException(409,"相同 request_id 正在处理")
        raise HTTPException(409,"相同 request_id 的调用已经失败，请更换 request_id")
    started=time.perf_counter()
    try:
        async def generate_one(values):
            output = await generate_names_v2(NameIn.model_validate(values), dev.user_id)
            try:
                return {"names": [item.model_dump() if hasattr(item, "model_dump") else dict(item) for item in output["names"]]}
            finally:
                await delete_naming_thread(output["thread_id"])
        if batch:
            results=[]
            for item in data:
                results.append(await generate_one(item))
            response={"results":results}
        else:
            response=await generate_one(data)
        await repo.finish(log.id,response,int((time.perf_counter()-started)*1000));return response
    except Exception as e:
        await repo.fail(log.id,str(e),int((time.perf_counter()-started)*1000));raise HTTPException(502,"命名服务暂时不可用，额度已返还")

@api_router.post("/names/generate",response_model=ApiNamingResult)
async def api_generate(data:ApiNamingIn,identity=Depends(api_identity),session:AsyncSession=Depends(get_session)):
    values=data.model_dump(exclude={"request_id","project_id"});return await execute(values,data.request_id,"names.generate",identity,session)

@api_router.post("/names/batch",response_model=ApiBatchResult)
async def api_batch(data:ApiBatchNamingIn,identity=Depends(api_identity),session:AsyncSession=Depends(get_session)):
    values=[x.model_dump(exclude={"project_id"}) for x in data.items];return await execute(values,data.request_id,"names.batch",identity,session,True)

@admin_router.get("",response_model=list[dict])
async def developers(admin_id:int=Depends(auth.require_permissions("developers.manage")),session:AsyncSession=Depends(get_session)):
    rows=await DeveloperRepository(session).developers();return [{**account_out(d),"username":u.username,"email":u.email} for d,u in rows]

@admin_router.post("/plans",response_model=ApiPlanOut)
async def create_plan(data:ApiPlanIn,request:Request,admin_id:int=Depends(auth.require_permissions("developers.manage")),session:AsyncSession=Depends(get_session)):
    x=await DeveloperRepository(session).create_plan(**data.model_dump());await SecurityRepository(session).audit(admin_user_id=admin_id,action="api.plan.create",target_type="api_plan",target_id=str(x.id),detail=json.dumps(data.model_dump(),default=str,ensure_ascii=False),ip_address=request_ip(request));return plan_out(x)

@admin_router.post("/{developer_id}/grant",response_model=ApiSubscriptionOut)
async def grant(developer_id:int,data:ApiGrantIn,request:Request,admin_id:int=Depends(auth.require_permissions("developers.manage")),session:AsyncSession=Depends(get_session)):
    repo=DeveloperRepository(session)
    try:x=await repo.grant(developer_id,data.plan_id);row=next(r for r in await repo.subscriptions(developer_id) if r[0].id==x.id)
    except LookupError as e:raise HTTPException(404,str(e))
    await SecurityRepository(session).audit(admin_user_id=admin_id,action="api.subscription.grant",target_type="developer_account",target_id=str(developer_id),detail=json.dumps(data.model_dump()),ip_address=request_ip(request));return sub_out(*row)

@admin_router.post("/{developer_id}/status",response_model=DeveloperOut)
async def developer_status(developer_id:int,data:DeveloperStatusIn,request:Request,admin_id:int=Depends(auth.require_permissions("developers.manage")),session:AsyncSession=Depends(get_session)):
    try:x=await DeveloperRepository(session).set_status(developer_id,data.status)
    except LookupError as e:raise HTTPException(404,str(e))
    await SecurityRepository(session).audit(admin_user_id=admin_id,action=f"developer.{data.status}",target_type="developer_account",target_id=str(developer_id),detail="{}",ip_address=request_ip(request));return account_out(x)
