import json
import os

from fastapi import APIRouter,Depends,HTTPException,Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from dependencies import get_session
from repository.growth_repo import GrowthRepository
from repository.security_repo import SecurityRepository
from routers.admin_router import request_ip
from schemas.growth_schemas import *

router=APIRouter(prefix="/growth",tags=["增长与分销"]);admin_router=APIRouter(prefix="/admin/growth",tags=["运营后台·增长"]);auth=AuthHandler()
def campaign_out(x):return {k:getattr(x,k) for k in ("id","name","description","inviter_reward","invitee_reward","commission_rate","starts_at","ends_at","is_active","created_at")}

@router.get("/promotion",response_model=PromotionOut)
async def promotion(user_id:int=Depends(auth.auth_access_dependency),session:AsyncSession=Depends(get_session)):
    repo=GrowthRepository(session);code=await repo.get_or_create_code(user_id);_,count,reward,commission=await repo.dashboard(user_id);base=os.getenv("FRONTEND_BASE_URL","http://127.0.0.1:5173").rstrip("/")
    return {"code":code.code,"invite_url":f"{base}/#register/{code.code}","invited_count":count,"reward_credits":reward,"commission_available":commission}

@router.get("/referrals",response_model=list[ReferralOut])
async def referrals(user_id:int=Depends(auth.auth_access_dependency),session:AsyncSession=Depends(get_session)):return [{"id":r.id,"username":u.username,"created_at":r.created_at} for r,u in await GrowthRepository(session).relations(user_id)]
@router.get("/rewards",response_model=list[RewardOut])
async def rewards(user_id:int=Depends(auth.auth_access_dependency),session:AsyncSession=Depends(get_session)):return [{k:getattr(x,k) for k in ("id","beneficiary_type","credit_count","status","created_at")} for x in await GrowthRepository(session).rewards(user_id)]
@router.get("/commissions",response_model=list[CommissionOut])
async def commissions(user_id:int=Depends(auth.auth_access_dependency),session:AsyncSession=Depends(get_session)):return [{"id":c.id,"order_no":o.order_no,"invitee_name":u.username,"order_amount":c.order_amount,"commission_rate":c.commission_rate,"commission_amount":c.commission_amount,"status":c.status,"created_at":c.created_at} for c,o,u in await GrowthRepository(session).commissions(user_id)]

@admin_router.get("/campaigns",response_model=list[CampaignOut])
async def campaigns(admin_id:int=Depends(auth.require_permissions("growth.manage")),session:AsyncSession=Depends(get_session)):return [campaign_out(x) for x in await GrowthRepository(session).campaigns()]
@admin_router.post("/campaigns",response_model=CampaignOut)
async def create_campaign(data:CampaignIn,request:Request,admin_id:int=Depends(auth.require_permissions("growth.manage")),session:AsyncSession=Depends(get_session)):
    x=await GrowthRepository(session).create_campaign(**data.model_dump());await SecurityRepository(session).audit(admin_user_id=admin_id,action="growth.campaign.create",target_type="growth_campaign",target_id=str(x.id),detail=json.dumps(data.model_dump(),default=str,ensure_ascii=False),ip_address=request_ip(request));return campaign_out(x)
@admin_router.post("/campaigns/{campaign_id}/status",response_model=CampaignOut)
async def campaign_status(campaign_id:int,data:CampaignStatusIn,request:Request,admin_id:int=Depends(auth.require_permissions("growth.manage")),session:AsyncSession=Depends(get_session)):
    try:x=await GrowthRepository(session).campaign_status(campaign_id,data.is_active)
    except LookupError as e:raise HTTPException(404,str(e))
    await SecurityRepository(session).audit(admin_user_id=admin_id,action="growth.campaign.status",target_type="growth_campaign",target_id=str(campaign_id),detail=json.dumps(data.model_dump()),ip_address=request_ip(request));return campaign_out(x)
@admin_router.get("/commissions",response_model=list[CommissionOut])
async def all_commissions(admin_id:int=Depends(auth.require_permissions("growth.manage")),session:AsyncSession=Depends(get_session)):return [{"id":c.id,"order_no":o.order_no,"invitee_name":u.username,"order_amount":c.order_amount,"commission_rate":c.commission_rate,"commission_amount":c.commission_amount,"status":c.status,"created_at":c.created_at} for c,o,u in await GrowthRepository(session).all_commissions()]
