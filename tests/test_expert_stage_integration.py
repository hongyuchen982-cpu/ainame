"""专家服务阶段的真实 MySQL 集成测试。"""

import unittest

import httpx
from sqlalchemy import delete, select

from core.redistools import redis_client
from main import app
from models import AsyncSessionFactory, engine
from models.auth_models import AdminAuditLog, Role, user_role
from models.expert_service import (
    ExpertDelivery,
    ExpertOrder,
    ExpertPackage,
    ExpertProfile,
    ExpertReview,
    ExpertSettlement,
)
from models.user import User


EXPERT_EMAIL = "__expert_stage_expert__@example.com"
CUSTOMER_EMAIL = "__expert_stage_customer__@example.com"
ADMIN_EMAIL = "__expert_stage_admin__@example.com"
PASSWORD = "TestPass123!"


class ExpertStageIntegrationTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await self.cleanup()
        async with AsyncSessionFactory() as session:
            async with session.begin():
                expert = User(email=EXPERT_EMAIL, username="测试命名专家", password=PASSWORD)
                customer = User(email=CUSTOMER_EMAIL, username="测试精批客户", password=PASSWORD)
                admin = User(email=ADMIN_EMAIL, username="测试专家管理员", password=PASSWORD)
                session.add_all([expert, customer, admin])
                await session.flush()
                roles = {
                    role.code: role.id
                    for role in await session.scalars(
                        select(Role).where(Role.code.in_(["member", "admin"]))
                    )
                }
                await session.execute(
                    user_role.insert(),
                    [
                        {"user_id": expert.id, "role_id": roles["member"]},
                        {"user_id": customer.id, "role_id": roles["member"]},
                        {"user_id": admin.id, "role_id": roles["member"]},
                        {"user_id": admin.id, "role_id": roles["admin"]},
                    ],
                )
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.cleanup()
        await redis_client.aclose()
        await engine.dispose()

    async def cleanup(self):
        async with AsyncSessionFactory() as session:
            async with session.begin():
                ids = list(
                    await session.scalars(
                        select(User.id).where(
                            User.email.in_([EXPERT_EMAIL, CUSTOMER_EMAIL, ADMIN_EMAIL])
                        )
                    )
                )
                if not ids:
                    return
                profile_ids = list(
                    await session.scalars(
                        select(ExpertProfile.id).where(ExpertProfile.user_id.in_(ids))
                    )
                )
                order_ids = list(
                    await session.scalars(
                        select(ExpertOrder.id).where(
                            (ExpertOrder.user_id.in_(ids))
                            | (ExpertOrder.expert_id.in_(profile_ids))
                        )
                    )
                )
                await session.execute(
                    delete(ExpertSettlement).where(ExpertSettlement.order_id.in_(order_ids))
                )
                await session.execute(
                    delete(ExpertReview).where(ExpertReview.order_id.in_(order_ids))
                )
                await session.execute(
                    delete(ExpertDelivery).where(ExpertDelivery.order_id.in_(order_ids))
                )
                await session.execute(delete(ExpertOrder).where(ExpertOrder.id.in_(order_ids)))
                await session.execute(
                    delete(ExpertPackage).where(ExpertPackage.expert_id.in_(profile_ids))
                )
                await session.execute(
                    delete(ExpertProfile).where(ExpertProfile.id.in_(profile_ids))
                )
                await session.execute(
                    delete(AdminAuditLog).where(AdminAuditLog.admin_user_id.in_(ids))
                )
                await session.execute(delete(user_role).where(user_role.c.user_id.in_(ids)))
                await session.execute(delete(User).where(User.id.in_(ids)))

    async def login(self, email):
        response = await self.client.post(
            "/auth/login", json={"email": email, "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    async def test_complete_expert_service_flow(self):
        expert_headers = await self.login(EXPERT_EMAIL)
        customer_headers = await self.login(CUSTOMER_EMAIL)
        admin_headers = await self.login(ADMIN_EMAIL)

        self.assertEqual(
            (await self.client.get("/admin/experts/applications", headers=customer_headers)).status_code,
            403,
        )
        self.assertEqual(
            (await self.client.get("/expert/packages", headers=expert_headers)).status_code,
            403,
        )

        application = await self.client.post(
            "/experts/apply",
            headers=expert_headers,
            json={
                "display_name": "清言老师",
                "title": "企业品牌命名顾问",
                "specialties": "企业命名、品牌战略、中文语义",
                "bio": "拥有多年企业品牌命名与中文语义研究经验，重视可用性、辨识度和长期品牌价值。",
                "experience_years": 8,
                "portfolio": "服务过科技、教育和消费品牌。",
            },
        )
        self.assertEqual(application.status_code, 200, application.text)
        profile_id = application.json()["id"]
        duplicate_application = await self.client.post(
            "/experts/apply",
            headers=expert_headers,
            json={**application.json(), "bio": application.json()["bio"]},
        )
        self.assertEqual(duplicate_application.status_code, 400)

        reviewed = await self.client.post(
            f"/admin/experts/applications/{profile_id}/review",
            headers=admin_headers,
            json={"status": "approved", "review_note": "资质与案例审核通过"},
        )
        self.assertEqual(reviewed.status_code, 200, reviewed.text)
        self.assertEqual(reviewed.json()["status"], "approved")

        # 审核前签发的 access token 也应通过实时权限查询获得专家能力。
        package = await self.client.post(
            "/expert/packages",
            headers=expert_headers,
            json={
                "name": "企业名称深度精批",
                "description": "从语义、传播、行业适配和品牌延展四个方向提供完整的名称分析与建议。",
                "price": "699.00",
                "delivery_days": 5,
                "revision_count": 1,
            },
        )
        self.assertEqual(package.status_code, 200, package.text)
        package_id = package.json()["id"]
        public_packages = await self.client.get("/experts/packages")
        self.assertEqual(public_packages.status_code, 200, public_packages.text)
        self.assertTrue(any(item["id"] == package_id for item in public_packages.json()))

        own_order = await self.client.post(
            "/experts/orders",
            headers=expert_headers,
            json={
                "package_id": package_id,
                "requirement": "专家本人不应当能够购买自己的服务套餐，这是一条边界条件测试需求。",
                "client_request_id": "expert-stage-self-order",
            },
        )
        self.assertEqual(own_order.status_code, 400)

        payload = {
            "package_id": package_id,
            "requirement": "需要分析候选企业名称的语义辨识度、行业适配、传播风险与后续品牌延展空间。",
            "client_request_id": "expert-stage-customer-order",
        }
        order = await self.client.post(
            "/experts/orders", headers=customer_headers, json=payload
        )
        duplicate_order = await self.client.post(
            "/experts/orders", headers=customer_headers, json=payload
        )
        self.assertEqual(order.status_code, 200, order.text)
        self.assertEqual(duplicate_order.status_code, 200, duplicate_order.text)
        self.assertEqual(order.json()["id"], duplicate_order.json()["id"])
        order_id = order.json()["id"]

        accepted = await self.client.post(
            f"/expert/orders/{order_id}/accept", headers=expert_headers
        )
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(accepted.json()["status"], "accepted")
        delivery = await self.client.post(
            f"/expert/orders/{order_id}/deliver",
            headers=expert_headers,
            json={
                "title": "企业名称深度精批交付报告",
                "content": "该名称在中文语义上清晰积极，读音节奏稳定，具备较好的行业适配性。建议在正式使用前继续完成商标、工商和域名检索，并以统一视觉系统强化差异化识别。",
                "attachment_url": "",
            },
        )
        self.assertEqual(delivery.status_code, 200, delivery.text)
        self.assertEqual(delivery.json()["status"], "delivered")

        review = await self.client.post(
            f"/experts/orders/{order_id}/review",
            headers=customer_headers,
            json={"rating": 5, "content": "分析完整，建议具有实际可执行性。"},
        )
        self.assertEqual(review.status_code, 200, review.text)
        self.assertEqual(review.json()["status"], "completed")
        self.assertEqual(
            (
                await self.client.post(
                    f"/experts/orders/{order_id}/review",
                    headers=customer_headers,
                    json={"rating": 5, "content": "重复评价"},
                )
            ).status_code,
            400,
        )

        settlements = await self.client.get(
            "/expert/settlements", headers=expert_headers
        )
        self.assertEqual(settlements.status_code, 200, settlements.text)
        settlement = next(
            item for item in settlements.json() if item["order_id"] == order_id
        )
        self.assertEqual(settlement["gross_amount"], "699.00")
        self.assertEqual(settlement["platform_fee"], "69.90")
        self.assertEqual(settlement["net_amount"], "629.10")
        settlement_id = settlement["id"]
        self.assertEqual(
            (
                await self.client.post(
                    f"/admin/experts/settlements/{settlement_id}/settle",
                    headers=customer_headers,
                )
            ).status_code,
            403,
        )
        settled = await self.client.post(
            f"/admin/experts/settlements/{settlement_id}/settle",
            headers=admin_headers,
        )
        settled_again = await self.client.post(
            f"/admin/experts/settlements/{settlement_id}/settle",
            headers=admin_headers,
        )
        self.assertEqual(settled.status_code, 200, settled.text)
        self.assertEqual(settled_again.status_code, 200, settled_again.text)
        self.assertEqual(settled.json()["status"], "settled")


if __name__ == "__main__":
    unittest.main()
