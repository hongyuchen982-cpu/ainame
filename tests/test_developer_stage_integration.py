"""B 端开放平台阶段的真实 MySQL 集成测试。"""

import hashlib
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from sqlalchemy import delete, select

from core.redistools import redis_client
from main import app
from models import AsyncSessionFactory, engine
from models.auth_models import AdminAuditLog, Role, user_role
from models.developer_platform import ApiPlan, ApiUsageLog, DeveloperAccount, DeveloperApiKey, DeveloperSubscription
from models.user import User


DEV_EMAIL = "__developer_stage_user__@example.com"
ADMIN_EMAIL = "__developer_stage_admin__@example.com"
PASSWORD = "TestPass123!"


class DeveloperStageIntegrationTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await self.cleanup()
        async with AsyncSessionFactory() as session:
            async with session.begin():
                developer = User(email=DEV_EMAIL, username="开放平台测试用户", password=PASSWORD)
                admin = User(email=ADMIN_EMAIL, username="开放平台管理员", password=PASSWORD)
                session.add_all([developer, admin]); await session.flush()
                roles = {x.code:x.id for x in await session.scalars(select(Role).where(Role.code.in_(["member","admin"])))}
                await session.execute(user_role.insert(), [{"user_id":developer.id,"role_id":roles["member"]},{"user_id":admin.id,"role_id":roles["member"]},{"user_id":admin.id,"role_id":roles["admin"]}])
        self.client=httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://testserver")

    async def asyncTearDown(self):
        await self.client.aclose();await self.cleanup();await redis_client.aclose();await engine.dispose()

    async def cleanup(self):
        async with AsyncSessionFactory() as session:
            async with session.begin():
                user_ids=list(await session.scalars(select(User.id).where(User.email.in_([DEV_EMAIL,ADMIN_EMAIL]))))
                if not user_ids:return
                developer_ids=list(await session.scalars(select(DeveloperAccount.id).where(DeveloperAccount.user_id.in_(user_ids))))
                key_ids=list(await session.scalars(select(DeveloperApiKey.id).where(DeveloperApiKey.developer_id.in_(developer_ids))))
                sub_ids=list(await session.scalars(select(DeveloperSubscription.id).where(DeveloperSubscription.developer_id.in_(developer_ids))))
                await session.execute(delete(ApiUsageLog).where((ApiUsageLog.developer_id.in_(developer_ids))|ApiUsageLog.api_key_id.in_(key_ids)))
                await session.execute(delete(DeveloperSubscription).where(DeveloperSubscription.id.in_(sub_ids)))
                await session.execute(delete(DeveloperApiKey).where(DeveloperApiKey.id.in_(key_ids)))
                await session.execute(delete(DeveloperAccount).where(DeveloperAccount.id.in_(developer_ids)))
                await session.execute(delete(ApiPlan).where(ApiPlan.name.like("__developer_stage_%")))
                await session.execute(delete(AdminAuditLog).where(AdminAuditLog.admin_user_id.in_(user_ids)))
                await session.execute(delete(user_role).where(user_role.c.user_id.in_(user_ids)))
                await session.execute(delete(User).where(User.id.in_(user_ids)))

    async def login(self,email):
        response=await self.client.post("/auth/login",json={"email":email,"password":PASSWORD});self.assertEqual(response.status_code,200,response.text)
        return {"Authorization":f"Bearer {response.json()['access_token']}"}

    async def test_complete_developer_platform_flow(self):
        dev_headers=await self.login(DEV_EMAIL);admin_headers=await self.login(ADMIN_EMAIL)
        self.assertEqual((await self.client.get("/admin/developers",headers=dev_headers)).status_code,403)
        account=await self.client.post("/developers/account",headers=dev_headers,json={"company_name":"测试科技有限公司","contact_name":"测试联系人","use_case":"将中文智能命名能力集成到企业内部品牌管理系统。"})
        self.assertEqual(account.status_code,200,account.text);developer_id=account.json()["id"]
        key=await self.client.post("/developers/keys",headers=dev_headers,json={"name":"生产测试 Key"})
        self.assertEqual(key.status_code,200,key.text);raw_key=key.json()["api_key"];key_id=key.json()["id"]
        self.assertTrue(raw_key.startswith("qmk_live_"));self.assertNotIn(raw_key,repr((await self.client.get("/developers/keys",headers=dev_headers)).json()))
        async with AsyncSessionFactory() as session:
            stored=await session.get(DeveloperApiKey,key_id)
            self.assertEqual(stored.key_hash,hashlib.sha256(raw_key.encode()).hexdigest());self.assertNotEqual(stored.key_hash,raw_key)
        plans=await self.client.get("/developers/plans",headers=dev_headers);self.assertEqual(plans.status_code,200,plans.text)
        free=next(x for x in plans.json() if x["price"]=="0.00")
        subscribed=await self.client.post(f"/developers/plans/{free['id']}/subscribe",headers=dev_headers)
        self.assertEqual(subscribed.status_code,200,subscribed.text);self.assertEqual(subscribed.json()["quota_remaining"],20)
        generated={"thread_id":"__developer_stage_api_thread__","names":[{"name":"星序","reference":"星辰秩序","moral":"清晰有序","domain":"xingxu.com","domain_status":"可注册"}]}
        payload={"request_id":"developer-single-request","category":"企业名","surname":"","gender":"不限","length":"两字","other":"科技协作平台","exclude":[]}
        with patch("routers.developer_router.generate_names_v2",new=AsyncMock(return_value=generated)) as mocked, patch("routers.developer_router.delete_naming_thread",new=AsyncMock()) as deleted:
            first=await self.client.post("/openapi/v1/names/generate",headers={"X-API-Key":raw_key},json=payload)
            duplicate=await self.client.post("/openapi/v1/names/generate",headers={"X-API-Key":raw_key},json=payload)
        self.assertEqual(first.status_code,200,first.text);self.assertEqual(first.json(),duplicate.json());self.assertEqual(mocked.await_count,1);self.assertEqual(mocked.await_args.args[0].category,"企业名");deleted.assert_awaited_once_with("__developer_stage_api_thread__")
        conflict=await self.client.post("/openapi/v1/names/batch",headers={"X-API-Key":raw_key},json={"request_id":payload["request_id"],"items":[{k:v for k,v in payload.items() if k!="request_id"}]})
        self.assertEqual(conflict.status_code,409,conflict.text)
        batch_payload={"request_id":"developer-batch-failed","items":[{"category":"宠物名","surname":"","gender":"不限","length":"两字","other":"活泼","exclude":[]},{"category":"企业名","surname":"","gender":"不限","length":"两字","other":"教育科技","exclude":[]}]}
        with patch("routers.developer_router.generate_names_v2",new=AsyncMock(side_effect=RuntimeError("forced provider error"))):
            failed=await self.client.post("/openapi/v1/names/batch",headers={"X-API-Key":raw_key},json=batch_payload)
        self.assertEqual(failed.status_code,502,failed.text)
        subs=await self.client.get("/developers/subscriptions",headers=dev_headers);self.assertEqual(subs.json()[0]["quota_used"],1)
        usage=await self.client.get("/developers/usage",headers=dev_headers);self.assertEqual(len(usage.json()),2);self.assertEqual({x["status"] for x in usage.json()},{"success","failed"})
        summary=await self.client.get("/developers/usage/summary",headers=dev_headers);self.assertEqual(summary.json(),{"calls_total":2,"units_total":3,"success_total":1,"failed_total":1})
        paid_plan=await self.client.post("/admin/developers/plans",headers=admin_headers,json={"name":"__developer_stage_business__","description":"合同制调用套餐","price":"999.00","quota_calls":1000,"validity_days":365})
        self.assertEqual(paid_plan.status_code,200,paid_plan.text)
        self.assertEqual((await self.client.post(f"/developers/plans/{paid_plan.json()['id']}/subscribe",headers=dev_headers)).status_code,400)
        granted=await self.client.post(f"/admin/developers/{developer_id}/grant",headers=admin_headers,json={"plan_id":paid_plan.json()["id"]})
        self.assertEqual(granted.status_code,200,granted.text);self.assertEqual(granted.json()["quota_total"],1000)
        second_key=await self.client.post("/developers/keys",headers=dev_headers,json={"name":"停用测试 Key"});self.assertEqual(second_key.status_code,200,second_key.text)
        revoked=await self.client.delete(f"/developers/keys/{key_id}",headers=dev_headers);self.assertEqual(revoked.status_code,200,revoked.text)
        self.assertEqual((await self.client.post("/openapi/v1/names/generate",headers={"X-API-Key":raw_key},json={**payload,"request_id":"after-revoke"})).status_code,401)
        suspended=await self.client.post(f"/admin/developers/{developer_id}/status",headers=admin_headers,json={"status":"suspended"});self.assertEqual(suspended.status_code,200,suspended.text)
        self.assertEqual((await self.client.post("/openapi/v1/names/generate",headers={"X-API-Key":second_key.json()["api_key"]},json={**payload,"request_id":"after-suspend"})).status_code,401)


if __name__=="__main__":unittest.main()
