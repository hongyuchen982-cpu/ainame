import secrets
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.growth import GrowthCampaign, PromotionCode, ReferralCommission, ReferralRelation, ReferralReward
from models.user import User
from models.user_credit import CreditLog, UserCredit
from models.user_order import UserOrder


class GrowthRepository:
    def __init__(self,session:AsyncSession):self.session=session

    async def get_or_create_code(self,user_id:int):
        async with self.session.begin():
            item=await self.session.scalar(select(PromotionCode).where(PromotionCode.user_id==user_id).with_for_update())
            if item:return item
            for _ in range(5):
                code=secrets.token_hex(4).upper()
                if not await self.session.scalar(select(PromotionCode.id).where(PromotionCode.code==code)):break
            item=PromotionCode(user_id=user_id,code=code);self.session.add(item);await self.session.flush();return item

    async def bind_registration_in_transaction(self,invitee_id:int,code:str|None):
        if not code:return None
        promotion=await self.session.scalar(select(PromotionCode).where(PromotionCode.code==code.upper(),PromotionCode.status=="active").with_for_update())
        if not promotion:raise ValueError("邀请码无效")
        if promotion.user_id==invitee_id:raise ValueError("不能邀请自己")
        campaign=await self.session.scalar(select(GrowthCampaign).where(GrowthCampaign.is_active.is_(True),GrowthCampaign.starts_at<=datetime.now(),GrowthCampaign.ends_at>datetime.now()).order_by(GrowthCampaign.id.desc()).limit(1))
        relation=ReferralRelation(inviter_id=promotion.user_id,invitee_id=invitee_id,promotion_code_id=promotion.id,campaign_id=campaign.id if campaign else None)
        self.session.add(relation);await self.session.flush()
        if campaign:
            await self._grant(relation.id,promotion.user_id,"inviter",campaign.inviter_reward)
            await self._grant(relation.id,invitee_id,"invitee",campaign.invitee_reward)
        return relation

    async def dashboard(self,user_id:int):
        async with self.session.begin():
            code=await self.session.scalar(select(PromotionCode).where(PromotionCode.user_id==user_id))
            invited=await self.session.scalar(select(func.count(ReferralRelation.id)).where(ReferralRelation.inviter_id==user_id)) or 0
            rewards=await self.session.scalar(select(func.coalesce(func.sum(ReferralReward.credit_count),0)).where(ReferralReward.user_id==user_id,ReferralReward.status=="granted")) or 0
            commission=await self.session.scalar(select(func.coalesce(func.sum(ReferralCommission.commission_amount),0)).where(ReferralCommission.inviter_id==user_id,ReferralCommission.status=="available")) or Decimal("0")
            return code,invited,rewards,commission

    async def relations(self,user_id:int):
        async with self.session.begin():return list((await self.session.execute(select(ReferralRelation,User).join(User,User.id==ReferralRelation.invitee_id).where(ReferralRelation.inviter_id==user_id).order_by(ReferralRelation.id.desc()))).all())
    async def rewards(self,user_id:int):
        async with self.session.begin():return list(await self.session.scalars(select(ReferralReward).where(ReferralReward.user_id==user_id).order_by(ReferralReward.id.desc())))
    async def commissions(self,user_id:int):
        async with self.session.begin():return list((await self.session.execute(select(ReferralCommission,UserOrder,User).join(UserOrder,UserOrder.id==ReferralCommission.order_id).join(ReferralRelation,ReferralRelation.id==ReferralCommission.relation_id).join(User,User.id==ReferralRelation.invitee_id).where(ReferralCommission.inviter_id==user_id).order_by(ReferralCommission.id.desc()))).all())

    async def create_commission_in_transaction(self,order:UserOrder):
        if await self.session.scalar(select(ReferralCommission.id).where(ReferralCommission.order_id==order.id)):return None
        relation=await self.session.scalar(select(ReferralRelation).where(ReferralRelation.invitee_id==order.user_id))
        if not relation or not relation.campaign_id:return None
        campaign=await self.session.get(GrowthCampaign,relation.campaign_id)
        if not campaign or campaign.commission_rate<=0:return None
        amount=(Decimal(order.amount)*Decimal(campaign.commission_rate)).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
        if amount<=0:return None
        item=ReferralCommission(relation_id=relation.id,order_id=order.id,inviter_id=relation.inviter_id,order_amount=order.amount,commission_rate=campaign.commission_rate,commission_amount=amount)
        self.session.add(item);await self.session.flush();return item

    async def reverse_commission_in_transaction(self,order_id:int):
        item=await self.session.scalar(select(ReferralCommission).where(ReferralCommission.order_id==order_id).with_for_update())
        if item and item.status=="available":item.status,item.reversed_at="reversed",datetime.now()
        return item

    async def campaigns(self):
        async with self.session.begin():return list(await self.session.scalars(select(GrowthCampaign).order_by(GrowthCampaign.id.desc())))
    async def create_campaign(self,**values):
        async with self.session.begin():
            item=GrowthCampaign(**values);self.session.add(item);await self.session.flush();return item
    async def campaign_status(self,campaign_id:int,active:bool):
        async with self.session.begin():
            item=await self.session.get(GrowthCampaign,campaign_id,with_for_update=True)
            if not item:raise LookupError("增长活动不存在")
            item.is_active=active;return item
    async def all_commissions(self):
        async with self.session.begin():return list((await self.session.execute(select(ReferralCommission,UserOrder,User).join(UserOrder,UserOrder.id==ReferralCommission.order_id).join(ReferralRelation,ReferralRelation.id==ReferralCommission.relation_id).join(User,User.id==ReferralRelation.invitee_id).order_by(ReferralCommission.id.desc()))).all())

    async def _grant(self,relation_id,user_id,kind,count):
        if count<=0:return
        credit=await self.session.scalar(select(UserCredit).where(UserCredit.user_id==user_id).with_for_update())
        if not credit:raise ValueError("邀请奖励账户不存在")
        credit.balance+=count
        reward=ReferralReward(relation_id=relation_id,user_id=user_id,beneficiary_type=kind,credit_count=count);self.session.add(reward);await self.session.flush()
        self.session.add(CreditLog(user_id=user_id,change_count=count,balance_after=credit.balance,type="invite_reward",remark="邀请好友活动奖励",operation_id=f"invite:{relation_id}:{kind}"))
