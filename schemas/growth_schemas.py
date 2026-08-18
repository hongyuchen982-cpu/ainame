from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator

class CampaignIn(BaseModel):
    name:str=Field(...,min_length=2,max_length=120);description:str=Field("",max_length=500)
    inviter_reward:int=Field(0,ge=0,le=10000);invitee_reward:int=Field(0,ge=0,le=10000)
    commission_rate:Decimal=Field(0,ge=0,le=0.5,decimal_places=4)
    starts_at:datetime;ends_at:datetime
    @model_validator(mode="after")
    def dates(self):
        if self.ends_at<=self.starts_at:raise ValueError("活动结束时间必须晚于开始时间")
        return self
class CampaignOut(CampaignIn): id:int;is_active:bool;created_at:datetime
class PromotionOut(BaseModel): code:str;invite_url:str;invited_count:int;reward_credits:int;commission_available:Decimal
class ReferralOut(BaseModel): id:int;username:str;created_at:datetime
class RewardOut(BaseModel): id:int;beneficiary_type:str;credit_count:int;status:str;created_at:datetime
class CommissionOut(BaseModel): id:int;order_no:str;invitee_name:str;order_amount:Decimal;commission_rate:Decimal;commission_amount:Decimal;status:str;created_at:datetime
class CampaignStatusIn(BaseModel): is_active:bool
