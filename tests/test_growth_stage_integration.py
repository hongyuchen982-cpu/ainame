"""增长与分销阶段的真实 MySQL/Redis 集成测试。"""
import unittest
from datetime import datetime,timedelta
from decimal import Decimal
from unittest.mock import AsyncMock,patch
import httpx
from sqlalchemy import delete,select
from core.redistools import redis_client
from dependencies import get_email
from main import app
from models import AsyncSessionFactory,engine
from models.auth_models import AdminAuditLog,Role,user_role
from models.growth import GrowthCampaign,PromotionCode,ReferralCommission,ReferralRelation,ReferralReward
from models.package import Package
from models.payment_transaction import PaymentTransaction
from models.user import User
from models.user_credit import CreditLog,UserCredit
from models.user_order import UserOrder
from repository.growth_repo import GrowthRepository
from repository.order_repo import OrderRepository

INVITER="__growth_stage_inviter__@example.com";INVITEE="__growth_stage_invitee__@example.com";INVALID="__growth_stage_invalid__@example.com";ADMIN="__growth_stage_admin__@example.com";PASSWORD="TestPass123!"
class FakeMail:
    async def send_message(self,message):pass
class GrowthStageIntegrationTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await self.cleanup()
        await self.cleanup_redis()
        async with AsyncSessionFactory() as s:
            async with s.begin():
                inviter=User(email=INVITER,username="增长邀请用户",password=PASSWORD);admin=User(email=ADMIN,username="增长管理员",password=PASSWORD);s.add_all([inviter,admin]);await s.flush()
                roles={x.code:x.id for x in await s.scalars(select(Role).where(Role.code.in_(["member","admin"])))};await s.execute(user_role.insert(),[{"user_id":inviter.id,"role_id":roles["member"]},{"user_id":admin.id,"role_id":roles["member"]},{"user_id":admin.id,"role_id":roles["admin"]}])
                s.add_all([UserCredit(user_id=inviter.id,balance=3,total_used=0,total_recharge=0),CreditLog(user_id=inviter.id,change_count=3,balance_after=3,type="register_gift",remark="测试")])
        self.client=httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://testserver");app.dependency_overrides[get_email]=lambda:FakeMail()
    async def asyncTearDown(self):
        await self.client.aclose();app.dependency_overrides.pop(get_email,None);await self.cleanup_redis();await self.cleanup();await redis_client.aclose();await engine.dispose()
    async def cleanup_redis(self):
        keys=[]
        for email in (INVITEE,INVALID):
            keys.extend([f"register:code:{email}",f"rate:register-verify:{email}",f"rate:register-code:email:{email}"])
        async for key in redis_client.scan_iter(match="rate:register-code:ip:*"):keys.append(key)
        if keys:await redis_client.delete(*keys)
    async def cleanup(self):
        async with AsyncSessionFactory() as s:
            async with s.begin():
                ids=list(await s.scalars(select(User.id).where(User.email.in_([INVITER,INVITEE,INVALID,ADMIN]))))
                if not ids:return
                order_ids=list(await s.scalars(select(UserOrder.id).where(UserOrder.user_id.in_(ids))))
                relation_ids=list(await s.scalars(select(ReferralRelation.id).where((ReferralRelation.inviter_id.in_(ids))|(ReferralRelation.invitee_id.in_(ids)))))
                await s.execute(delete(ReferralCommission).where((ReferralCommission.order_id.in_(order_ids))|ReferralCommission.relation_id.in_(relation_ids)))
                await s.execute(delete(ReferralReward).where(ReferralReward.relation_id.in_(relation_ids)));await s.execute(delete(ReferralRelation).where(ReferralRelation.id.in_(relation_ids)))
                await s.execute(delete(PromotionCode).where(PromotionCode.user_id.in_(ids)));await s.execute(delete(PaymentTransaction).where(PaymentTransaction.order_id.in_(order_ids)));await s.execute(delete(UserOrder).where(UserOrder.id.in_(order_ids)))
                await s.execute(delete(CreditLog).where(CreditLog.user_id.in_(ids)));await s.execute(delete(UserCredit).where(UserCredit.user_id.in_(ids)));await s.execute(delete(AdminAuditLog).where(AdminAuditLog.admin_user_id.in_(ids)));await s.execute(delete(user_role).where(user_role.c.user_id.in_(ids)));await s.execute(delete(User).where(User.id.in_(ids)))
                await s.execute(delete(Package).where(Package.name=="__growth_stage_package__"));await s.execute(delete(GrowthCampaign).where(GrowthCampaign.name=="__growth_stage_campaign__"))
    async def login(self,email):
        r=await self.client.post("/auth/login",json={"email":email,"password":PASSWORD});self.assertEqual(r.status_code,200,r.text);return {"Authorization":f"Bearer {r.json()['access_token']}"}
    async def register(self,email,invite_code):
        sent=await self.client.get("/auth/code",params={"email":email});self.assertEqual(sent.status_code,200,sent.text);code=await redis_client.get(f"register:code:{email}")
        return await self.client.post("/auth/register",json={"email":email,"username":"受邀注册用户","password":PASSWORD,"confirm_password":PASSWORD,"code":code,"invite_code":invite_code})
    async def test_complete_growth_flow(self):
        inviter_headers=await self.login(INVITER);admin_headers=await self.login(ADMIN)
        created=await self.client.post("/admin/growth/campaigns",headers=admin_headers,json={"name":"__growth_stage_campaign__","description":"真实邀请奖励测试活动","inviter_reward":2,"invitee_reward":1,"commission_rate":"0.1000","starts_at":(datetime.now()-timedelta(days=1)).isoformat(),"ends_at":(datetime.now()+timedelta(days=10)).isoformat()});self.assertEqual(created.status_code,200,created.text)
        promotion=await self.client.get("/growth/promotion",headers=inviter_headers);self.assertEqual(promotion.status_code,200,promotion.text);code=promotion.json()["code"]
        invalid=await self.register(INVALID,"BADCODE9");self.assertEqual(invalid.status_code,400,invalid.text)
        async with AsyncSessionFactory() as s:self.assertIsNone(await s.scalar(select(User).where(User.email==INVALID)))
        registered=await self.register(INVITEE,code);self.assertEqual(registered.status_code,200,registered.text);invitee_headers=await self.login(INVITEE)
        self.assertEqual((await self.client.get("/credit/balance",headers=inviter_headers)).json()["balance"],5);self.assertEqual((await self.client.get("/credit/balance",headers=invitee_headers)).json()["balance"],4)
        async with AsyncSessionFactory() as s:
            async with s.begin():pkg=Package(name="__growth_stage_package__",price=Decimal("99.00"),description="测试",credit_count=10,is_active=True,sort_order=0);s.add(pkg);await s.flush();pkg_id=pkg.id
        async with AsyncSessionFactory() as s:invitee_id=await s.scalar(select(User.id).where(User.email==INVITEE))
        async with AsyncSessionFactory() as s:order,_=await OrderRepository(s).create_order(invitee_id,pkg_id,"growth-order-request");order_no=order.order_no
        async with AsyncSessionFactory() as s:paid,first=await OrderRepository(s).pay_success(order_no,"trade-growth");self.assertTrue(first)
        async with AsyncSessionFactory() as s:_,again=await OrderRepository(s).pay_success(order_no,"trade-growth");self.assertFalse(again)
        commissions=await self.client.get("/growth/commissions",headers=inviter_headers);self.assertEqual(len(commissions.json()),1);self.assertEqual(commissions.json()[0]["commission_amount"],"9.90")
        async with AsyncSessionFactory() as s:await OrderRepository(s).begin_refund(order_no,"growth-refund","测试退款")
        async with AsyncSessionFactory() as s:await OrderRepository(s).complete_refund(order_no,"growth-refund","success")
        after=await self.client.get("/growth/commissions",headers=inviter_headers);self.assertEqual(after.json()[0]["status"],"reversed")
        self.assertEqual((await self.client.get("/admin/growth/campaigns",headers=invitee_headers)).status_code,403)
if __name__=="__main__":unittest.main()
