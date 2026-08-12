"""用户与权限第一阶段的真实 MySQL/Redis 集成测试。

运行：python -m unittest tests.test_auth_stage_integration -v
测试只使用 __auth_stage_test__ 命名空间，并在结束后清理自身数据。
"""

import base64
import asyncio
import io
import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pdfplumber
from sqlalchemy import delete, select

from core.redistools import redis_client
from dependencies import get_email
from main import app
from models import AsyncSessionFactory, engine
from models.auth_models import (
    AdminAuditLog,
    LoginRecord,
    Role,
    UserDevice,
    role_permission,
    user_role,
)
from models.user import User
from models.user_credit import CreditLog, UserCredit
from models.package import Package
from models.user_order import UserOrder
from models.payment_transaction import PaymentTransaction
from models.knowledge_file import KnowledgeFile
from models.async_task import AsyncTask
from models.name_validation import NameValidation
from models.brand_asset import BrandAsset
from models.naming_report import NamingReport
from repository.security_repo import SecurityRepository
from repository.credit_repo import CreditRepository
from repository.knowledge_repo import KnowledgeRepository
from repository.task_repo import TaskRepository
from rag_worker import process_message
from core.name_validation_service import calculate_risk
from schemas.brand_asset_schemas import BrandAssetGenerated


MEMBER_EMAIL = "__auth_stage_test_member__@example.com"
ADMIN_EMAIL = "__auth_stage_test_admin__@example.com"
REGISTER_EMAIL = "__auth_stage_test_register__@example.com"
FAILED_REGISTER_EMAIL = "__auth_stage_test_failed_register__@example.com"
ATTACK_EMAIL = "__auth_stage_test_attack__@example.com"
TEST_ROLE = "auth_stage_test_auditor"
OLD_PASSWORD = "TestPass123!"
NEW_PASSWORD = "NewPass123!"
RESET_PASSWORD = "ResetPass123!"
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


class FakeMail:
    async def send_message(self, message):
        return None


class AuthStageIntegrationTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await self.cleanup_test_data()
        async with AsyncSessionFactory() as session:
            async with session.begin():
                member = User(
                    email=MEMBER_EMAIL, username="测试普通用户", password=OLD_PASSWORD
                )
                admin = User(
                    email=ADMIN_EMAIL, username="测试管理员用户", password=OLD_PASSWORD
                )
                session.add_all([member, admin])
                await session.flush()
                roles = list(
                    await session.scalars(
                        select(Role).where(Role.code.in_(["member", "admin"]))
                    )
                )
                role_ids = {role.code: role.id for role in roles}
                await session.execute(
                    user_role.insert(),
                    [
                        {"user_id": member.id, "role_id": role_ids["member"]},
                        {"user_id": admin.id, "role_id": role_ids["member"]},
                        {"user_id": admin.id, "role_id": role_ids["admin"]},
                    ],
                )
                self.member_id = member.id
                self.admin_id = admin.id

        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        )
        app.dependency_overrides[get_email] = lambda: FakeMail()

    async def asyncTearDown(self):
        await self.client.aclose()
        app.dependency_overrides.pop(get_email, None)
        await redis_client.delete(f"password-reset:code:{MEMBER_EMAIL}")
        await redis_client.delete(f"register:code:{REGISTER_EMAIL}")
        await redis_client.delete(f"register:code:{FAILED_REGISTER_EMAIL}")
        rate_keys = []
        async for key in redis_client.scan_iter(match="rate:*"):
            if (
                MEMBER_EMAIL in key
                or ADMIN_EMAIL in key
                or REGISTER_EMAIL in key
                or FAILED_REGISTER_EMAIL in key
                or ATTACK_EMAIL in key
                or key.endswith(":127.0.0.1")
            ):
                rate_keys.append(key)
        if rate_keys:
            await redis_client.delete(*rate_keys)
        avatar_dir = Path(__file__).resolve().parents[1] / "static" / "avatars"
        for avatar in avatar_dir.glob(f"{self.member_id}_*"):
            avatar.unlink(missing_ok=True)
        await self.cleanup_test_data()
        await redis_client.aclose()
        await engine.dispose()

    async def cleanup_test_data(self):
        async with AsyncSessionFactory() as session:
            async with session.begin():
                await session.execute(
                    delete(UserOrder).where(
                        UserOrder.order_no.like("__auth_stage_order%")
                    )
                )
                ids = list(
                    await session.scalars(
                        select(User.id).where(
                            User.email.in_(
                                [
                                    MEMBER_EMAIL,
                                    ADMIN_EMAIL,
                                    REGISTER_EMAIL,
                                    FAILED_REGISTER_EMAIL,
                                ]
                            )
                        )
                    )
                )
                test_role_id = await session.scalar(
                    select(Role.id).where(Role.code == TEST_ROLE)
                )
                if ids:
                    report_filenames = list(
                        await session.scalars(
                            select(NamingReport.filename).where(
                                NamingReport.user_id.in_(ids)
                            )
                        )
                    )
                    order_ids = select(UserOrder.id).where(UserOrder.user_id.in_(ids))
                    await session.execute(
                        delete(PaymentTransaction).where(
                            PaymentTransaction.order_id.in_(order_ids)
                        )
                    )
                    await session.execute(
                        delete(UserOrder).where(UserOrder.user_id.in_(ids))
                    )
                    await session.execute(
                        delete(AdminAuditLog).where(
                            AdminAuditLog.admin_user_id.in_(ids)
                        )
                    )
                    await session.execute(
                        delete(LoginRecord).where(
                            LoginRecord.email.in_(
                                [
                                    MEMBER_EMAIL,
                                    ADMIN_EMAIL,
                                    REGISTER_EMAIL,
                                    FAILED_REGISTER_EMAIL,
                                    ATTACK_EMAIL,
                                ]
                            )
                        )
                    )
                    await session.execute(
                        delete(UserDevice).where(UserDevice.user_id.in_(ids))
                    )
                    await session.execute(
                        delete(CreditLog).where(CreditLog.user_id.in_(ids))
                    )
                    await session.execute(
                        delete(UserCredit).where(UserCredit.user_id.in_(ids))
                    )
                    await session.execute(
                        delete(AsyncTask).where(AsyncTask.user_id.in_(ids))
                    )
                    await session.execute(
                        delete(NamingReport).where(NamingReport.user_id.in_(ids))
                    )
                    for filename in report_filenames:
                        (
                            Path(__file__).resolve().parents[1]
                            / "output"
                            / "pdf"
                            / Path(filename).name
                        ).unlink(missing_ok=True)
                    await session.execute(
                        delete(BrandAsset).where(BrandAsset.user_id.in_(ids))
                    )
                    await session.execute(
                        delete(NameValidation).where(NameValidation.user_id.in_(ids))
                    )
                    await session.execute(
                        delete(KnowledgeFile).where(KnowledgeFile.user_id.in_(ids))
                    )
                    await session.execute(
                        delete(user_role).where(user_role.c.user_id.in_(ids))
                    )
                    await session.execute(delete(User).where(User.id.in_(ids)))
                await session.execute(
                    delete(Package).where(Package.name.like("__auth_stage_pkg%"))
                )
                if test_role_id:
                    await session.execute(
                        delete(role_permission).where(
                            role_permission.c.role_id == test_role_id
                        )
                    )
                    await session.execute(
                        delete(user_role).where(user_role.c.role_id == test_role_id)
                    )
                    await session.execute(delete(Role).where(Role.id == test_role_id))

    async def login(self, email: str, password: str) -> dict:
        response = await self.client.post(
            "/auth/login", json={"email": email, "password": password}
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    @staticmethod
    def bearer(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    async def test_complete_user_permission_flow(self):
        send_code = await self.client.get(
            "/auth/code", params={"email": REGISTER_EMAIL}
        )
        self.assertEqual(send_code.status_code, 200, send_code.text)
        register_code = await redis_client.get(f"register:code:{REGISTER_EMAIL}")
        self.assertEqual(len(register_code), 6)
        registered = await self.client.post(
            "/auth/register",
            json={
                "email": REGISTER_EMAIL,
                "username": "测试注册用户",
                "password": OLD_PASSWORD,
                "confirm_password": OLD_PASSWORD,
                "code": register_code,
            },
        )
        self.assertEqual(registered.status_code, 200, registered.text)
        registered_login = await self.login(REGISTER_EMAIL, OLD_PASSWORD)
        registered_user_id = registered_login["user"]["id"]
        registered_balance = await self.client.get(
            "/credit/balance",
            headers=self.bearer(registered_login["access_token"]),
        )
        self.assertEqual(registered_balance.status_code, 200, registered_balance.text)
        self.assertEqual(registered_balance.json()["balance"], 3)

        # 命名项目：自动创建、候选轮次、反馈历史、最终选名和归档。
        registered_headers = self.bearer(registered_login["access_token"])
        first_candidates = [
            {
                "name": "星澜",
                "reference": "星河与清澜",
                "moral": "明亮开阔",
                "domain": "xinglan.com",
                "domain_status": "待查询",
            },
            {
                "name": "云舟",
                "reference": "云海行舟",
                "moral": "自在坚定",
                "domain": "yunzhou.com",
                "domain_status": "待查询",
            },
        ]
        with patch(
            "routers.name_router.generate_names_v2",
            new=AsyncMock(
                return_value={
                    "thread_id": "__auth_stage_project_thread__",
                    "names": first_candidates,
                }
            ),
        ):
            generated = await self.client.post(
                "/name/generate",
                headers=registered_headers,
                json={
                    "category": "宠物名",
                    "surname": "",
                    "gender": "不限",
                    "length": "两字",
                    "other": "活泼的金毛",
                    "exclude": [],
                },
            )
        self.assertEqual(generated.status_code, 200, generated.text)
        project_id = generated.json()["project_id"]
        project_detail = await self.client.get(
            f"/projects/{project_id}", headers=registered_headers
        )
        self.assertEqual(project_detail.status_code, 200, project_detail.text)
        self.assertEqual(project_detail.json()["current_round"], 1)
        self.assertEqual(len(project_detail.json()["rounds"][0]["candidates"]), 2)

        second_candidates = [
            {
                "name": "暖星",
                "reference": "温暖星光",
                "moral": "温柔陪伴",
                "domain": "nuanxing.com",
                "domain_status": "待查询",
            }
        ]
        with patch(
            "routers.name_router.get_naming_state",
            new=AsyncMock(return_value={"user_id": registered_user_id}),
        ), patch(
            "routers.name_router.feedback_names",
            new=AsyncMock(
                return_value={
                    "thread_id": "__auth_stage_project_thread__",
                    "data": {"names": second_candidates},
                }
            ),
        ):
            feedback = await self.client.post(
                "/name/feedback",
                headers=registered_headers,
                json={
                    "thread_id": "__auth_stage_project_thread__",
                    "category": "宠物名",
                    "feedback": "更温暖一些",
                },
            )
        self.assertEqual(feedback.status_code, 200, feedback.text)
        self.assertEqual(feedback.json()["project_id"], project_id)

        with patch(
            "routers.name_router.get_naming_candidates",
            new=AsyncMock(return_value=("宠物名", second_candidates)),
        ):
            selected_project_name = await self.client.post(
                "/name/select",
                headers=registered_headers,
                json={
                    "thread_id": "__auth_stage_project_thread__",
                    "name": "暖星",
                },
            )
        self.assertEqual(
            selected_project_name.status_code, 200, selected_project_name.text
        )
        self.assertEqual(selected_project_name.json()["project_id"], project_id)

        projects = await self.client.get("/projects", headers=registered_headers)
        self.assertEqual(projects.status_code, 200, projects.text)
        self.assertTrue(any(item["id"] == project_id for item in projects.json()))
        detail_after_select = await self.client.get(
            f"/projects/{project_id}", headers=registered_headers
        )
        self.assertEqual(detail_after_select.json()["status"], "selected")
        self.assertEqual(detail_after_select.json()["current_round"], 2)
        self.assertEqual(detail_after_select.json()["final_selection"]["name"], "暖星")

        archived = await self.client.post(
            f"/projects/{project_id}/archive", headers=registered_headers
        )
        self.assertEqual(archived.status_code, 200, archived.text)
        self.assertEqual(archived.json()["status"], "archived")
        blocked_feedback = await self.client.post(
            "/name/feedback",
            headers=registered_headers,
            json={
                "thread_id": "__auth_stage_project_thread__",
                "category": "宠物名",
                "feedback": "归档后不应继续",
            },
        )
        self.assertEqual(blocked_feedback.status_code, 403, blocked_feedback.text)
        restored = await self.client.post(
            f"/projects/{project_id}/restore", headers=registered_headers
        )
        self.assertEqual(restored.json()["status"], "selected")

        draft = await self.client.post(
            "/projects",
            headers=registered_headers,
            json={
                "title": "我的企业命名草稿",
                "conditions": {
                    "category": "企业名",
                    "surname": "",
                    "gender": "不限",
                    "length": "不限",
                    "other": "人工智能教育品牌",
                    "exclude": [],
                },
            },
        )
        self.assertEqual(draft.status_code, 200, draft.text)
        renamed = await self.client.patch(
            f"/projects/{draft.json()['id']}",
            headers=registered_headers,
            json={
                "title": "AI 教育品牌命名",
                "conditions": {
                    "category": "企业名",
                    "surname": "",
                    "gender": "不限",
                    "length": "两字",
                    "other": "面向青少年的人工智能教育品牌",
                    "exclude": ["智"],
                },
            },
        )
        self.assertEqual(renamed.json()["title"], "AI 教育品牌命名")
        updated_draft_detail = await self.client.get(
            f"/projects/{draft.json()['id']}", headers=registered_headers
        )
        self.assertEqual(updated_draft_detail.json()["conditions"]["length"], "两字")

        # 同一草稿的并发首次生成只允许一个请求进入 AI 和扣次事务。
        concurrent_candidates = [
            {
                "name": "并发星",
                "reference": "并发测试",
                "moral": "只生成一次",
                "domain": "concurrent-star.com",
                "domain_status": "待查询",
            }
        ]

        async def slow_generate(*_args, **_kwargs):
            await asyncio.sleep(0.15)
            return {
                "thread_id": "__auth_stage_concurrent_thread__",
                "names": concurrent_candidates,
            }

        generate_mock = AsyncMock(side_effect=slow_generate)
        generate_payload = {
            "project_id": draft.json()["id"],
            "category": "企业名",
            "surname": "",
            "gender": "不限",
            "length": "两字",
            "other": "面向青少年的人工智能教育品牌",
            "exclude": ["智"],
        }
        with patch("routers.name_router.generate_names_v2", new=generate_mock):
            concurrent_generate = await asyncio.gather(
                *[
                    self.client.post(
                        "/name/generate",
                        headers=registered_headers,
                        json=generate_payload,
                    )
                    for _ in range(2)
                ]
            )
        self.assertEqual(
            sorted(item.status_code for item in concurrent_generate), [200, 409]
        )
        self.assertEqual(generate_mock.await_count, 1)

        # 同一 thread 的并发反馈同样只能执行一次，并保存一个新轮次。
        async def slow_feedback(*_args, **_kwargs):
            await asyncio.sleep(0.15)
            return {
                "thread_id": "__auth_stage_concurrent_thread__",
                "data": {"names": concurrent_candidates},
            }

        feedback_mock = AsyncMock(side_effect=slow_feedback)
        previous_state = {
            "user_id": registered_user_id,
            "category": "企业名",
            "final_output": {"names": concurrent_candidates},
        }
        feedback_payload = {
            "thread_id": "__auth_stage_concurrent_thread__",
            "category": "企业名",
            "feedback": "更简洁",
        }
        with patch(
            "routers.name_router.get_naming_state",
            new=AsyncMock(return_value=previous_state),
        ), patch("routers.name_router.feedback_names", new=feedback_mock):
            concurrent_feedback = await asyncio.gather(
                *[
                    self.client.post(
                        "/name/feedback",
                        headers=registered_headers,
                        json=feedback_payload,
                    )
                    for _ in range(2)
                ]
            )
        self.assertEqual(
            sorted(item.status_code for item in concurrent_feedback), [200, 409]
        )
        self.assertEqual(feedback_mock.await_count, 1)

        # 参数不一致是 400；业务库失败时必须补偿恢复 LangGraph 状态。
        category_mismatch = await self.client.post(
            "/name/feedback",
            headers=registered_headers,
            json={**feedback_payload, "category": "宠物名"},
        )
        self.assertEqual(category_mismatch.status_code, 400, category_mismatch.text)

        restore_mock = AsyncMock()
        with patch(
            "routers.name_router.get_naming_state",
            new=AsyncMock(return_value=previous_state),
        ), patch(
            "routers.name_router.feedback_names",
            new=AsyncMock(
                return_value={
                    "thread_id": "__auth_stage_concurrent_thread__",
                    "data": {"names": concurrent_candidates},
                }
            ),
        ), patch(
            "routers.name_router.NamingProjectRepository.append_round",
            new=AsyncMock(side_effect=RuntimeError("forced mysql failure")),
        ), patch(
            "routers.name_router.restore_naming_state",
            new=restore_mock,
        ):
            compensated = await self.client.post(
                "/name/feedback",
                headers=registered_headers,
                json=feedback_payload,
            )
        self.assertEqual(compensated.status_code, 500, compensated.text)
        restore_mock.assert_awaited_once_with(
            "__auth_stage_concurrent_thread__",
            registered_user_id,
            previous_state,
        )

        # 企业最终选名可进行综合校验；请求幂等且未知数据源不能误报低风险。
        enterprise_selection = await self.client.post(
            "/name/select",
            headers=registered_headers,
            json={
                "thread_id": "__auth_stage_concurrent_thread__",
                "name": "并发星",
            },
        )
        self.assertEqual(
            enterprise_selection.status_code, 200, enterprise_selection.text
        )
        enterprise_selection_id = enterprise_selection.json()["id"]
        mocked_validation = {
            "status": "completed",
            "domains": [
                {
                    "domain": "concurrent-star.com",
                    "status": "registered",
                    "message": "已注册",
                },
                {
                    "domain": "concurrent-star.cn",
                    "status": "available",
                    "message": "可注册",
                },
            ],
            "trademark": {
                "status": "completed",
                "matches": [{"name": "并发星", "similarity": 1.0}],
                "message": "查询完成",
            },
            "company": {
                "status": "completed",
                "matches": [{"name": "并发星科技", "similarity": 0.8}],
                "message": "查询完成",
            },
            "social": {
                "status": "completed",
                "profiles": [{"platform": "demo", "status": "occupied"}],
                "message": "查询完成",
            },
            "score": 72,
            "level": "high",
            "coverage": 100,
            "summary": "发现高度近似商标；存在域名和社交平台占用",
        }
        validation_payload = {
            "selected_name_id": enterprise_selection_id,
            "client_request_id": "__auth_stage_validation_request__",
            "domain_stem": "concurrent-star",
            "suffixes": ["com", "cn"],
        }
        validation_mock = AsyncMock(return_value=mocked_validation)
        with patch(
            "routers.validation_router.run_name_validation", new=validation_mock
        ):
            validation = await self.client.post(
                "/validations", headers=registered_headers, json=validation_payload
            )
            duplicate_validation = await self.client.post(
                "/validations", headers=registered_headers, json=validation_payload
            )
        self.assertEqual(validation.status_code, 200, validation.text)
        self.assertEqual(
            duplicate_validation.status_code, 200, duplicate_validation.text
        )
        self.assertEqual(validation.json()["id"], duplicate_validation.json()["id"])
        self.assertEqual(validation.json()["risk_level"], "high")
        self.assertEqual(validation_mock.await_count, 1)
        validation_id = validation.json()["id"]
        validation_history = await self.client.get(
            f"/validations?selected_name_id={enterprise_selection_id}",
            headers=registered_headers,
        )
        self.assertEqual(validation_history.status_code, 200, validation_history.text)
        self.assertTrue(
            any(item["id"] == validation_id for item in validation_history.json())
        )
        invalid_stem = await self.client.post(
            "/validations",
            headers=registered_headers,
            json={
                **validation_payload,
                "client_request_id": "__invalid_stem_request__",
                "domain_stem": "bad.stem",
            },
        )
        self.assertEqual(invalid_stem.status_code, 422, invalid_stem.text)
        no_coverage = calculate_risk(
            [{"domain": "x.invalid", "status": "unknown"}],
            {"status": "unavailable", "matches": []},
            {"status": "unavailable", "matches": []},
            {"status": "unavailable", "profiles": []},
        )
        self.assertEqual(no_coverage["level"], "unknown")
        self.assertEqual(no_coverage["coverage"], 0)
        high_risk = calculate_risk(
            [{"domain": "x.com", "status": "registered"}],
            {"status": "completed", "matches": [{"similarity": 0.96}]},
            {"status": "completed", "matches": [{"similarity": 1.0}]},
            {"status": "completed", "profiles": [{"status": "occupied"}]},
        )
        self.assertEqual(high_risk["level"], "high")
        self.assertEqual(high_risk["coverage"], 100)

        # 品牌价值资产：关联最终企业名与校验快照，重复请求保持幂等。
        generated_asset = BrandAssetGenerated.model_validate(
            {
                "positioning": {
                    "target_audience": "重视效率的成长型科技企业",
                    "market_category": "企业智能协作服务",
                    "core_value": "让复杂协作清晰发生",
                    "brand_personality": ["清晰", "可信", "进取"],
                    "differentiation": "以东方语义和智能流程形成差异",
                    "positioning_statement": "面向成长型企业的智能协作品牌。",
                },
                "slogans": [
                    {
                        "text": "并发灵感，共赴新程",
                        "tone": "进取",
                        "rationale": "呼应名称与协作价值",
                    },
                    {
                        "text": "让每一步，同频向前",
                        "tone": "温暖",
                        "rationale": "强调团队一致行动",
                    },
                    {
                        "text": "汇聚所想，成就所向",
                        "tone": "稳健",
                        "rationale": "表达聚合与兑现",
                    },
                ],
                "logo_concepts": [
                    {
                        "title": "星轨汇聚",
                        "symbol": "多条轨迹汇聚成星",
                        "composition": "横向组合标",
                        "colors": ["深海蓝", "晨曦金"],
                        "typography": "现代无衬线字体",
                        "rationale": "表达协作汇聚",
                    },
                    {
                        "title": "并行之门",
                        "symbol": "双线构成开放门户",
                        "composition": "方形图标加字标",
                        "colors": ["墨黑", "活力红"],
                        "typography": "几何黑体",
                        "rationale": "体现并行与开放",
                    },
                ],
                "visual_guidelines": {
                    "colors": [
                        {"name": "深海蓝", "hex": "#173B57", "usage": "主品牌色"},
                        {"name": "晨曦金", "hex": "#D99B5E", "usage": "强调色"},
                        {"name": "云白", "hex": "#F8F6F1", "usage": "背景色"},
                    ],
                    "typography": "标题使用现代黑体，正文保证易读性",
                    "imagery": "采用轨迹、光点与真实协作场景",
                    "layout": "留白充足，使用清晰模块化网格",
                    "avoid": ["过度科技蓝", "复杂渐变", "未经核实的认证标识"],
                },
                "risk_notes": [
                    {
                        "category": "品牌辨识",
                        "level": "medium",
                        "note": "名称含常见意象",
                        "action": "强化独特图形资产",
                    },
                    {
                        "category": "使用合规",
                        "level": "high",
                        "note": "校验发现近似项",
                        "action": "提交注册前咨询商标专业人士",
                    },
                ],
            }
        )
        asset_payload = {
            "selected_name_id": enterprise_selection_id,
            "validation_id": validation_id,
            "client_request_id": "__auth_stage_brand_asset_request__",
            "brief": "面向成长型科技企业，气质清晰可信。",
        }
        asset_mock = AsyncMock(return_value=generated_asset)
        with patch(
            "routers.brand_asset_router.generate_brand_asset_content", new=asset_mock
        ):
            asset = await self.client.post(
                "/brand-assets", headers=registered_headers, json=asset_payload
            )
            duplicate_asset = await self.client.post(
                "/brand-assets", headers=registered_headers, json=asset_payload
            )
        self.assertEqual(asset.status_code, 200, asset.text)
        self.assertEqual(duplicate_asset.status_code, 200, duplicate_asset.text)
        self.assertEqual(asset.json()["id"], duplicate_asset.json()["id"])
        self.assertEqual(asset_mock.await_count, 1)
        self.assertEqual(asset.json()["domain_matrix"][0]["status"], "registered")
        self.assertEqual(asset.json()["validation_snapshot"]["risk_level"], "high")
        brand_asset_id = asset.json()["id"]
        asset_history = await self.client.get(
            f"/brand-assets?selected_name_id={enterprise_selection_id}",
            headers=registered_headers,
        )
        self.assertEqual(asset_history.status_code, 200, asset_history.text)
        self.assertTrue(
            any(item["id"] == brand_asset_id for item in asset_history.json())
        )
        with patch(
            "routers.brand_asset_router.generate_brand_asset_content",
            new=AsyncMock(side_effect=RuntimeError("forced ai failure")),
        ):
            failed_asset = await self.client.post(
                "/brand-assets",
                headers=registered_headers,
                json={
                    **asset_payload,
                    "client_request_id": "__auth_stage_brand_asset_failed__",
                },
            )
        self.assertEqual(failed_asset.status_code, 502, failed_asset.text)

        # PDF 报告汇总项目、候选、最终选名、校验与品牌资产，并通过鉴权下载。
        report_payload = {
            "project_id": draft.json()["id"],
            "validation_id": validation_id,
            "brand_asset_id": brand_asset_id,
            "client_request_id": "__auth_stage_report_request__",
        }
        report = await self.client.post(
            "/reports", headers=registered_headers, json=report_payload
        )
        duplicate_report = await self.client.post(
            "/reports", headers=registered_headers, json=report_payload
        )
        self.assertEqual(report.status_code, 200, report.text)
        self.assertEqual(duplicate_report.status_code, 200, duplicate_report.text)
        self.assertEqual(report.json()["id"], duplicate_report.json()["id"])
        self.assertGreaterEqual(report.json()["page_count"], 5)
        report_id = report.json()["id"]
        report_history = await self.client.get("/reports", headers=registered_headers)
        self.assertEqual(report_history.status_code, 200, report_history.text)
        self.assertTrue(any(item["id"] == report_id for item in report_history.json()))
        report_download = await self.client.get(
            f"/reports/{report_id}/download", headers=registered_headers
        )
        self.assertEqual(report_download.status_code, 200, report_download.text)
        self.assertTrue(report_download.content.startswith(b"%PDF"))
        self.assertEqual(
            report_download.headers["x-report-sha256"], report.json()["sha256"]
        )
        with pdfplumber.open(io.BytesIO(report_download.content)) as document:
            report_text = "\n".join(
                page.extract_text() or "" for page in document.pages
            )
        self.assertIn("并发星", report_text)
        self.assertIn("Slogan", report_text)

        dashboard = await self.client.get(
            "/users/me/dashboard", headers=registered_headers
        )
        self.assertEqual(dashboard.status_code, 200, dashboard.text)
        dashboard_data = dashboard.json()
        self.assertGreaterEqual(dashboard_data["projects_total"], 1)
        self.assertGreaterEqual(dashboard_data["projects_selected"], 1)
        self.assertGreaterEqual(dashboard_data["credit_logs"], 1)
        self.assertGreaterEqual(dashboard_data["reports_total"], 1)
        self.assertTrue(
            any(item["id"] == report_id for item in dashboard_data["recent_reports"])
        )
        with patch(
            "routers.report_router.generate_naming_report_pdf",
            side_effect=RuntimeError("forced pdf failure"),
        ):
            failed_report = await self.client.post(
                "/reports",
                headers=registered_headers,
                json={
                    **report_payload,
                    "client_request_id": "__auth_stage_report_failed__",
                },
            )
        self.assertEqual(failed_report.status_code, 500, failed_report.text)

        # 扣次与失败返还都以 operation_id 保证幂等，重复调用不重复变更余额。
        async with AsyncSessionFactory() as credit_session:
            credit_repo = CreditRepository(credit_session)
            balance_before_refund = await credit_repo.get_balance(registered_user_id)
            refunded_once = await credit_repo.refund_name_credit(
                registered_user_id,
                "name:__auth_stage_project_thread__",
                "集成测试模拟生成失败返还",
            )
            refunded_twice = await credit_repo.refund_name_credit(
                registered_user_id,
                "name:__auth_stage_project_thread__",
                "集成测试模拟生成失败返还",
            )
        self.assertEqual(refunded_once, balance_before_refund + 1)
        self.assertEqual(refunded_twice, refunded_once)

        credit_account = await self.client.get(
            "/credit/account", headers=registered_headers
        )
        credit_logs = await self.client.get("/credit/logs", headers=registered_headers)
        self.assertEqual(credit_account.status_code, 200, credit_account.text)
        self.assertEqual(credit_account.json()["balance"], refunded_once)
        self.assertEqual(
            len(
                [
                    item
                    for item in credit_logs.json()
                    if item["operation_id"]
                    == "refund:name:__auth_stage_project_thread__"
                ]
            ),
            1,
        )

        # 项目只能由所属用户读取。
        project_admin_login = await self.login(ADMIN_EMAIL, OLD_PASSWORD)
        owner_isolation = await self.client.get(
            f"/projects/{project_id}",
            headers=self.bearer(project_admin_login["access_token"]),
        )
        self.assertEqual(owner_isolation.status_code, 404, owner_isolation.text)

        # 普通用户无权进入次数后台；管理员调整与重复请求必须幂等。
        member_credit_admin = await self.client.get(
            "/admin/credits", headers=registered_headers
        )
        self.assertEqual(member_credit_admin.status_code, 403, member_credit_admin.text)
        admin_headers = self.bearer(project_admin_login["access_token"])
        admin_validations = await self.client.get(
            "/admin/validations", headers=admin_headers
        )
        self.assertEqual(admin_validations.status_code, 200, admin_validations.text)
        self.assertTrue(
            any(item["id"] == validation_id for item in admin_validations.json())
        )
        self.assertEqual(
            (
                await self.client.get("/admin/validations", headers=registered_headers)
            ).status_code,
            403,
        )
        self.assertEqual(
            (
                await self.client.get(
                    f"/validations/{validation_id}", headers=admin_headers
                )
            ).status_code,
            404,
        )
        admin_assets = await self.client.get(
            "/admin/brand-assets", headers=admin_headers
        )
        self.assertEqual(admin_assets.status_code, 200, admin_assets.text)
        self.assertTrue(
            any(item["id"] == brand_asset_id for item in admin_assets.json())
        )
        self.assertEqual(
            (
                await self.client.get("/admin/brand-assets", headers=registered_headers)
            ).status_code,
            403,
        )
        self.assertEqual(
            (
                await self.client.get(
                    f"/brand-assets/{brand_asset_id}", headers=admin_headers
                )
            ).status_code,
            404,
        )
        admin_reports = await self.client.get("/admin/reports", headers=admin_headers)
        self.assertEqual(admin_reports.status_code, 200, admin_reports.text)
        self.assertTrue(any(item["id"] == report_id for item in admin_reports.json()))
        self.assertEqual(
            (
                await self.client.get("/admin/reports", headers=registered_headers)
            ).status_code,
            403,
        )
        self.assertEqual(
            (
                await self.client.get(f"/reports/{report_id}", headers=admin_headers)
            ).status_code,
            404,
        )
        admin_report_download = await self.client.get(
            f"/admin/reports/{report_id}/download", headers=admin_headers
        )
        self.assertEqual(
            admin_report_download.status_code, 200, admin_report_download.text
        )
        admin_dashboard = await self.client.get(
            "/admin/dashboard", headers=admin_headers
        )
        self.assertEqual(admin_dashboard.status_code, 200, admin_dashboard.text)
        self.assertGreaterEqual(admin_dashboard.json()["users_total"], 2)
        self.assertGreaterEqual(admin_dashboard.json()["projects_total"], 1)
        self.assertGreaterEqual(admin_dashboard.json()["reports_total"], 1)
        self.assertEqual(
            (
                await self.client.get(
                    "/admin/dashboard", headers=registered_headers
                )
            ).status_code,
            403,
        )
        admin_projects = await self.client.get(
            "/admin/projects?status=selected", headers=admin_headers
        )
        self.assertEqual(admin_projects.status_code, 200, admin_projects.text)
        self.assertTrue(
            any(item["id"] == project_id for item in admin_projects.json())
        )
        self.assertEqual(
            (
                await self.client.get(
                    "/admin/projects", headers=registered_headers
                )
            ).status_code,
            403,
        )
        admin_credit_list = await self.client.get(
            "/admin/credits", headers=admin_headers
        )
        self.assertEqual(admin_credit_list.status_code, 200, admin_credit_list.text)
        adjust_payload = {
            "change_count": 4,
            "remark": "集成测试管理员增加次数",
            "operation_id": "admin:__auth_stage_credit_adjust__",
        }
        adjusted_once = await self.client.post(
            f"/admin/users/{registered_user_id}/credits",
            headers=admin_headers,
            json=adjust_payload,
        )
        adjusted_twice = await self.client.post(
            f"/admin/users/{registered_user_id}/credits",
            headers=admin_headers,
            json=adjust_payload,
        )
        self.assertEqual(adjusted_once.status_code, 200, adjusted_once.text)
        self.assertEqual(adjusted_twice.status_code, 200, adjusted_twice.text)
        self.assertEqual(adjusted_once.json()["balance"], refunded_once + 4)
        self.assertEqual(
            adjusted_twice.json()["balance"], adjusted_once.json()["balance"]
        )

        # 套餐后台：权限、增改、上下架、排序、公开列表和安全删除。
        member_packages_admin = await self.client.get(
            "/admin/packages", headers=registered_headers
        )
        self.assertEqual(
            member_packages_admin.status_code, 403, member_packages_admin.text
        )
        package_payloads = [
            {
                "name": "__auth_stage_pkg_basic__",
                "description": "基础套餐",
                "price": "9.90",
                "credit_count": 5,
                "is_active": True,
                "sort_order": 20,
            },
            {
                "name": "__auth_stage_pkg_pro__",
                "description": "进阶套餐",
                "price": "19.90",
                "credit_count": 12,
                "is_active": True,
                "sort_order": 10,
            },
        ]
        created_packages = []
        for payload in package_payloads:
            response = await self.client.post(
                "/admin/packages", headers=admin_headers, json=payload
            )
            self.assertEqual(response.status_code, 200, response.text)
            created_packages.append(response.json())
        basic, pro = created_packages

        public_packages = await self.client.get("/package/list")
        public_test_ids = [
            item["id"]
            for item in public_packages.json()
            if item["id"] in {basic["id"], pro["id"]}
        ]
        self.assertEqual(public_test_ids, [pro["id"], basic["id"]])

        updated_package = await self.client.patch(
            f"/admin/packages/{basic['id']}",
            headers=admin_headers,
            json={"price": "12.50", "credit_count": 7, "description": "已更新"},
        )
        self.assertEqual(updated_package.status_code, 200, updated_package.text)
        self.assertEqual(updated_package.json()["price"], "12.50")
        null_update = await self.client.patch(
            f"/admin/packages/{basic['id']}",
            headers=admin_headers,
            json={"price": None},
        )
        self.assertEqual(null_update.status_code, 422, null_update.text)

        sorted_packages = await self.client.put(
            "/admin/packages/sort",
            headers=admin_headers,
            json={
                "items": [
                    {"id": basic["id"], "sort_order": 1},
                    {"id": pro["id"], "sort_order": 2},
                ]
            },
        )
        self.assertEqual(sorted_packages.status_code, 200, sorted_packages.text)
        self.assertEqual(
            [item["id"] for item in sorted_packages.json()], [basic["id"], pro["id"]]
        )

        deactivated = await self.client.post(
            f"/admin/packages/{basic['id']}/status",
            headers=admin_headers,
            json={"is_active": False},
        )
        self.assertEqual(deactivated.status_code, 200, deactivated.text)
        public_after_deactivate = await self.client.get("/package/list")
        self.assertNotIn(
            basic["id"], [item["id"] for item in public_after_deactivate.json()]
        )
        inactive_purchase = await self.client.post(
            "/pay/create_order",
            headers=registered_headers,
            json={"package_id": basic["id"]},
        )
        self.assertEqual(inactive_purchase.status_code, 400, inactive_purchase.text)

        async with AsyncSessionFactory() as order_session:
            async with order_session.begin():
                order_session.add(
                    UserOrder(
                        order_no="__auth_stage_order_package_guard__",
                        user_id=registered_user_id,
                        package_id=pro["id"],
                        amount=pro["price"],
                        credit_count=pro["credit_count"],
                        status="pending",
                        alipay_trade_no="",
                    )
                )
        protected_delete = await self.client.delete(
            f"/admin/packages/{pro['id']}", headers=admin_headers
        )
        self.assertEqual(protected_delete.status_code, 409, protected_delete.text)
        async with AsyncSessionFactory() as order_session:
            async with order_session.begin():
                await order_session.execute(
                    delete(UserOrder).where(
                        UserOrder.order_no == "__auth_stage_order_package_guard__"
                    )
                )

        class FakeAlipay:
            query_result = {}

            def api_alipay_trade_page_pay(self, **kwargs):
                return f"out_trade_no={kwargs['out_trade_no']}"

            def api_alipay_trade_query(self, **kwargs):
                return self.query_result

            def api_alipay_trade_close(self, **kwargs):
                return {"code": "10000", "msg": "Success"}

            def api_alipay_trade_refund(self, **kwargs):
                return {"code": "10000", "msg": "Success", "fund_change": "Y"}

        fake_alipay = FakeAlipay()
        with patch("routers.pay_router.create_alipay", return_value=fake_alipay), patch(
            "routers.pay_router.get_alipay_gateway",
            return_value="https://example.test/pay",
        ), patch(
            "routers.pay_router.get_return_url",
            return_value="https://example.test/return",
        ), patch(
            "routers.pay_router.get_notify_url",
            return_value="https://example.test/notify",
        ):
            order_request = "__auth_stage_order_idempotent__"
            created_order = await self.client.post(
                "/pay/create_order",
                headers=registered_headers,
                json={"package_id": pro["id"], "client_request_id": order_request},
            )
            repeated_order = await self.client.post(
                "/pay/create_order",
                headers=registered_headers,
                json={"package_id": pro["id"], "client_request_id": order_request},
            )
            self.assertEqual(created_order.status_code, 200, created_order.text)
            self.assertEqual(
                repeated_order.json()["order_no"], created_order.json()["order_no"]
            )
            order_no = created_order.json()["order_no"]
            continued_payment = await self.client.post(
                f"/pay/orders/{order_no}/pay", headers=registered_headers
            )
            self.assertEqual(continued_payment.status_code, 200, continued_payment.text)
            self.assertEqual(continued_payment.json()["order_no"], order_no)

            concurrent_order_responses = await asyncio.gather(
                *[
                    self.client.post(
                        "/pay/create_order",
                        headers=registered_headers,
                        json={
                            "package_id": pro["id"],
                            "client_request_id": "__auth_stage_order_concurrent__",
                        },
                    )
                    for _ in range(2)
                ]
            )
            self.assertTrue(
                all(item.status_code == 200 for item in concurrent_order_responses)
            )
            self.assertEqual(
                len({item.json()["order_no"] for item in concurrent_order_responses}), 1
            )

            my_orders = await self.client.get("/pay/orders", headers=registered_headers)
            self.assertEqual(my_orders.status_code, 200, my_orders.text)
            self.assertTrue(
                any(item["order_no"] == order_no for item in my_orders.json())
            )
            order_detail = await self.client.get(
                f"/pay/orders/{order_no}/detail", headers=registered_headers
            )
            self.assertEqual(order_detail.status_code, 200, order_detail.text)
            self.assertEqual(order_detail.json()["transactions"], [])

            balance_before_payment = (
                await self.client.get("/credit/balance", headers=registered_headers)
            ).json()["balance"]
            fake_alipay.query_result = {
                "code": "10000",
                "trade_status": "TRADE_SUCCESS",
                "trade_no": "__auth_stage_alipay_trade__",
                "total_amount": created_order.json()["amount"],
            }
            synced = await self.client.post(
                f"/pay/orders/{order_no}/sync", headers=registered_headers
            )
            self.assertEqual(synced.status_code, 200, synced.text)
            self.assertEqual(synced.json()["status"], "paid")
            balance_after_payment = (
                await self.client.get("/credit/balance", headers=registered_headers)
            ).json()["balance"]
            self.assertEqual(
                balance_after_payment, balance_before_payment + pro["credit_count"]
            )

            paid_detail = await self.client.get(
                f"/pay/orders/{order_no}/detail", headers=registered_headers
            )
            self.assertEqual(len(paid_detail.json()["transactions"]), 1)
            admin_orders = await self.client.get("/admin/orders", headers=admin_headers)
            self.assertEqual(admin_orders.status_code, 200, admin_orders.text)
            self.assertTrue(
                any(item["order_no"] == order_no for item in admin_orders.json())
            )

            refunded = await self.client.post(
                f"/admin/orders/{order_no}/refund",
                headers=admin_headers,
                json={
                    "request_no": "__auth_stage_refund_request__",
                    "reason": "集成测试退款",
                },
            )
            self.assertEqual(refunded.status_code, 200, refunded.text)
            self.assertEqual(refunded.json()["status"], "refunded")
            balance_after_refund = (
                await self.client.get("/credit/balance", headers=registered_headers)
            ).json()["balance"]
            self.assertEqual(balance_after_refund, balance_before_payment)

            close_order = await self.client.post(
                "/pay/create_order",
                headers=registered_headers,
                json={
                    "package_id": pro["id"],
                    "client_request_id": "__auth_stage_order_close__",
                },
            )
            closed = await self.client.post(
                f"/pay/orders/{close_order.json()['order_no']}/close",
                headers=registered_headers,
            )
            self.assertEqual(closed.status_code, 200, closed.text)
            self.assertEqual(closed.json()["status"], "closed")

        async with AsyncSessionFactory() as order_session:
            async with order_session.begin():
                api_order_ids = select(UserOrder.id).where(
                    UserOrder.client_request_id.in_(
                        [
                            "__auth_stage_order_idempotent__",
                            "__auth_stage_order_close__",
                            "__auth_stage_order_concurrent__",
                        ]
                    )
                )
                await order_session.execute(
                    delete(PaymentTransaction).where(
                        PaymentTransaction.order_id.in_(api_order_ids)
                    )
                )
                await order_session.execute(
                    delete(UserOrder).where(
                        UserOrder.client_request_id.in_(
                            [
                                "__auth_stage_order_idempotent__",
                                "__auth_stage_order_close__",
                                "__auth_stage_order_concurrent__",
                            ]
                        )
                    )
                )

        for package in created_packages:
            deleted_package = await self.client.delete(
                f"/admin/packages/{package['id']}", headers=admin_headers
            )
            self.assertEqual(deleted_package.status_code, 200, deleted_package.text)

        # 注册任一步骤失败时，用户、次数和角色必须整体回滚。
        await redis_client.set(
            f"register:code:{FAILED_REGISTER_EMAIL}", "654321", ex=300
        )
        with patch.object(
            SecurityRepository,
            "assign_default_role_in_transaction",
            new=AsyncMock(side_effect=RuntimeError("模拟默认角色失败")),
        ):
            with self.assertRaises(RuntimeError):
                await self.client.post(
                    "/auth/register",
                    json={
                        "email": FAILED_REGISTER_EMAIL,
                        "username": "事务回滚用户",
                        "password": OLD_PASSWORD,
                        "confirm_password": OLD_PASSWORD,
                        "code": "654321",
                    },
                )
        async with AsyncSessionFactory() as session:
            failed_user = await session.scalar(
                select(User).where(User.email == FAILED_REGISTER_EMAIL)
            )
            self.assertIsNone(failed_user)

        member_login = await self.login(MEMBER_EMAIL, OLD_PASSWORD)
        admin_login = await self.login(ADMIN_EMAIL, OLD_PASSWORD)
        refreshed = await self.client.post(
            "/auth/refresh",
            headers=self.bearer(member_login["refresh_token"]),
        )
        self.assertEqual(refreshed.status_code, 200, refreshed.text)
        self.assertIn("refresh_token", refreshed.json())
        reused_refresh = await self.client.post(
            "/auth/refresh",
            headers=self.bearer(member_login["refresh_token"]),
        )
        self.assertEqual(reused_refresh.status_code, 401, reused_refresh.text)
        member_headers = self.bearer(refreshed.json()["access_token"])
        admin_headers = self.bearer(admin_login["access_token"])

        self.assertEqual((await self.client.get("/mail/test")).status_code, 404)

        profile = await self.client.get("/users/me", headers=member_headers)
        self.assertEqual(profile.status_code, 200, profile.text)
        self.assertIn("member", profile.json()["roles"])

        updated = await self.client.patch(
            "/users/me",
            headers=member_headers,
            json={"username": "修改后的测试用户"},
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["username"], "修改后的测试用户")

        avatar = await self.client.post(
            "/users/me/avatar",
            headers=member_headers,
            files={"file": ("avatar.png", PNG_1X1, "image/png")},
        )
        self.assertEqual(avatar.status_code, 200, avatar.text)
        self.assertTrue(avatar.json()["avatar_url"].startswith("/static/avatars/"))

        devices = await self.client.get("/users/me/devices", headers=member_headers)
        records = await self.client.get(
            "/users/me/login-records", headers=member_headers
        )
        self.assertEqual(devices.status_code, 200, devices.text)
        self.assertGreaterEqual(len(devices.json()), 1)
        self.assertTrue(any(record["success"] for record in records.json()))

        denied = await self.client.get("/admin/users", headers=member_headers)
        self.assertEqual(denied.status_code, 403, denied.text)
        allowed = await self.client.get("/admin/users", headers=admin_headers)
        self.assertEqual(allowed.status_code, 200, allowed.text)

        protected_system_role = await self.client.put(
            "/admin/roles/admin/permissions",
            headers=admin_headers,
            json={"permissions": []},
        )
        self.assertEqual(
            protected_system_role.status_code, 400, protected_system_role.text
        )
        self.assertEqual(
            (await self.client.get("/admin/users", headers=admin_headers)).status_code,
            200,
        )

        create_role = await self.client.post(
            "/admin/roles",
            headers=admin_headers,
            json={
                "code": TEST_ROLE,
                "name": "测试审计员",
                "description": "集成测试角色",
                "permissions": ["users.read"],
            },
        )
        self.assertEqual(create_role.status_code, 200, create_role.text)
        self.assertEqual(create_role.json()["permissions"], ["users.read"])
        update_permissions = await self.client.put(
            f"/admin/roles/{TEST_ROLE}/permissions",
            headers=admin_headers,
            json={"permissions": ["users.read"]},
        )
        self.assertEqual(update_permissions.status_code, 200, update_permissions.text)
        assign_role = await self.client.put(
            f"/admin/users/{self.member_id}/roles",
            headers=admin_headers,
            json={"roles": ["member", TEST_ROLE]},
        )
        self.assertEqual(assign_role.status_code, 200, assign_role.text)
        self.assertEqual(
            (await self.client.get("/users/me", headers=member_headers)).status_code,
            401,
        )
        member_login = await self.login(MEMBER_EMAIL, OLD_PASSWORD)
        self.assertIn("users.read", member_login["user"]["permissions"])
        member_headers = self.bearer(member_login["access_token"])
        custom_role_allowed = await self.client.get(
            "/admin/users", headers=member_headers
        )
        self.assertEqual(custom_role_allowed.status_code, 200, custom_role_allowed.text)

        freeze = await self.client.patch(
            f"/admin/users/{self.member_id}/status",
            headers=admin_headers,
            json={"status": "frozen"},
        )
        self.assertEqual(freeze.status_code, 200, freeze.text)
        frozen_access = await self.client.get("/users/me", headers=member_headers)
        self.assertEqual(frozen_access.status_code, 401, frozen_access.text)
        frozen_login = await self.client.post(
            "/auth/login",
            json={"email": MEMBER_EMAIL, "password": OLD_PASSWORD},
        )
        self.assertEqual(frozen_login.status_code, 403, frozen_login.text)

        unfreeze = await self.client.patch(
            f"/admin/users/{self.member_id}/status",
            headers=admin_headers,
            json={"status": "active"},
        )
        self.assertEqual(unfreeze.status_code, 200, unfreeze.text)
        member_login = await self.login(MEMBER_EMAIL, OLD_PASSWORD)
        member_headers = self.bearer(member_login["access_token"])

        changed = await self.client.post(
            "/users/me/password",
            headers=member_headers,
            json={
                "current_password": OLD_PASSWORD,
                "new_password": NEW_PASSWORD,
                "confirm_password": NEW_PASSWORD,
            },
        )
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(
            (await self.client.get("/users/me", headers=member_headers)).status_code,
            401,
        )

        reset_code_response = await self.client.post(
            "/auth/password-reset/code",
            json={"email": MEMBER_EMAIL},
        )
        self.assertEqual(reset_code_response.status_code, 200, reset_code_response.text)
        reset_code = await redis_client.get(f"password-reset:code:{MEMBER_EMAIL}")
        self.assertIsNotNone(reset_code)
        reset = await self.client.post(
            "/auth/password-reset/confirm",
            json={
                "email": MEMBER_EMAIL,
                "code": reset_code,
                "new_password": RESET_PASSWORD,
                "confirm_password": RESET_PASSWORD,
            },
        )
        self.assertEqual(reset.status_code, 200, reset.text)
        reused_code = await self.client.post(
            "/auth/password-reset/confirm",
            json={
                "email": MEMBER_EMAIL,
                "code": reset_code,
                "new_password": RESET_PASSWORD,
                "confirm_password": RESET_PASSWORD,
            },
        )
        self.assertEqual(reused_code.status_code, 400, reused_code.text)
        final_login = await self.login(MEMBER_EMAIL, RESET_PASSWORD)
        final_headers = self.bearer(final_login["access_token"])
        device_items = (
            await self.client.get("/users/me/devices", headers=final_headers)
        ).json()
        device_id = next(
            item["id"] for item in device_items if item["revoked_at"] is None
        )
        revoke = await self.client.delete(
            f"/users/me/devices/{device_id}", headers=final_headers
        )
        self.assertEqual(revoke.status_code, 200, revoke.text)
        self.assertEqual(
            (await self.client.get("/users/me", headers=final_headers)).status_code, 401
        )

        logout_login = await self.login(MEMBER_EMAIL, RESET_PASSWORD)
        logout_headers = self.bearer(logout_login["access_token"])
        logout = await self.client.post("/auth/logout", headers=logout_headers)
        self.assertEqual(logout.status_code, 200, logout.text)
        self.assertEqual(
            (await self.client.get("/users/me", headers=logout_headers)).status_code,
            401,
        )
        self.assertEqual(
            (
                await self.client.post(
                    "/auth/refresh",
                    headers=self.bearer(logout_login["refresh_token"]),
                )
            ).status_code,
            401,
        )

        audit = await self.client.get("/admin/audit-logs", headers=admin_headers)
        self.assertEqual(audit.status_code, 200, audit.text)
        self.assertTrue(any(item["action"] == "user.frozen" for item in audit.json()))

        traversal_name = r"folder\..\..\outside.txt"
        with patch("routers.rag_router.send_to_queue", new=AsyncMock()) as queue_mock:
            upload = await self.client.post(
                "/knowledge/upload",
                headers=admin_headers,
                files={"file": (traversal_name, b"safe test content", "text/plain")},
            )
            self.assertEqual(upload.status_code, 200, upload.text)
            queued_path = Path(queue_mock.await_args.args[0]["file_path"]).resolve()
            upload_root = (Path(__file__).resolve().parents[1] / "uploads").resolve()
            self.assertIn(upload_root, queued_path.parents)
            self.assertNotIn("outside", queued_path.name)
            knowledge_id = upload.json()["file"]["id"]
            task_id = upload.json()["task_id"]
            self.assertEqual(queue_mock.await_args.args[0]["task_id"], task_id)
            self.assertEqual(queue_mock.await_args.args[0]["file_id"], knowledge_id)
            self.assertEqual(queue_mock.await_args.args[0]["version"], 1)

        admin_files = await self.client.get("/knowledge/files", headers=admin_headers)
        self.assertEqual(admin_files.status_code, 200, admin_files.text)
        self.assertTrue(any(item["id"] == knowledge_id for item in admin_files.json()))
        knowledge_member_login = await self.login(MEMBER_EMAIL, RESET_PASSWORD)
        member_headers = self.bearer(knowledge_member_login["access_token"])
        self.assertEqual(
            (
                await self.client.get(
                    f"/knowledge/files/{knowledge_id}", headers=member_headers
                )
            ).status_code,
            404,
        )
        self.assertEqual(
            (
                await self.client.get("/admin/knowledge/files", headers=member_headers)
            ).status_code,
            403,
        )
        managed_files = await self.client.get(
            "/admin/knowledge/files", headers=admin_headers
        )
        self.assertEqual(managed_files.status_code, 200, managed_files.text)
        self.assertTrue(
            any(item["id"] == knowledge_id for item in managed_files.json())
        )
        self.assertEqual(
            (
                await self.client.get(f"/tasks/{task_id}", headers=member_headers)
            ).status_code,
            404,
        )
        self.assertEqual(
            (await self.client.get("/admin/tasks", headers=member_headers)).status_code,
            403,
        )
        admin_tasks = await self.client.get("/admin/tasks", headers=admin_headers)
        self.assertEqual(admin_tasks.status_code, 200, admin_tasks.text)
        self.assertTrue(any(item["id"] == task_id for item in admin_tasks.json()))

        worker_message = SimpleNamespace(
            body=json.dumps({"task_id": task_id}).encode(),
            ack=AsyncMock(),
            reject=AsyncMock(),
        )
        with patch("rag_worker.process_and_store_file", return_value=3):
            await process_message(worker_message)
        worker_message.ack.assert_awaited_once()
        worker_message.reject.assert_not_awaited()
        completed_task = await self.client.get(
            f"/tasks/{task_id}", headers=admin_headers
        )
        self.assertEqual(completed_task.json()["status"], "completed")
        self.assertEqual(completed_task.json()["progress"], 100)

        with patch("routers.rag_router.send_to_queue", new=AsyncMock()) as retry_queue:
            retried = await self.client.post(
                f"/knowledge/files/{knowledge_id}/reprocess", headers=admin_headers
            )
            self.assertEqual(retried.status_code, 200, retried.text)
            self.assertEqual(retried.json()["processing_version"], 2)
            self.assertEqual(retry_queue.await_args.args[0]["version"], 2)
            retry_task_id = retry_queue.await_args.args[0]["task_id"]
            duplicate_retry = await self.client.post(
                f"/knowledge/files/{knowledge_id}/reprocess", headers=admin_headers
            )
            self.assertEqual(duplicate_retry.status_code, 409, duplicate_retry.text)

        failed_worker_message = SimpleNamespace(
            body=json.dumps({"task_id": retry_task_id}).encode(),
            ack=AsyncMock(),
            reject=AsyncMock(),
        )
        with patch(
            "rag_worker.process_and_store_file",
            side_effect=RuntimeError("temporary failure"),
        ), patch("rag_worker.asyncio.sleep", new=AsyncMock()):
            await process_message(failed_worker_message)
            await process_message(failed_worker_message)
            await process_message(failed_worker_message)
        self.assertEqual(failed_worker_message.reject.await_count, 2)
        self.assertEqual(failed_worker_message.ack.await_count, 1)
        failed_task = await self.client.get(
            f"/tasks/{retry_task_id}", headers=admin_headers
        )
        self.assertEqual(failed_task.json()["status"], "failed")
        self.assertEqual(failed_task.json()["attempt_count"], 3)
        with patch(
            "routers.task_router.send_to_queue", new=AsyncMock()
        ) as user_task_retry:
            task_retried = await self.client.post(
                f"/tasks/{retry_task_id}/retry", headers=admin_headers
            )
            self.assertEqual(task_retried.status_code, 200, task_retried.text)
            self.assertEqual(
                user_task_retry.await_args.args[0]["task_id"], retry_task_id
            )
        async with AsyncSessionFactory() as session:
            self.assertIsNotNone(await TaskRepository(session).claim(retry_task_id))
        async with AsyncSessionFactory() as session:
            self.assertIsNotNone(
                await KnowledgeRepository(session).claim_processing(knowledge_id, 2)
            )
        with patch(
            "routers.rag_router.delete_knowledge_file_vectors",
            side_effect=RuntimeError("forced vector cleanup failure"),
        ):
            failed_delete = await self.client.delete(
                f"/admin/knowledge/files/{knowledge_id}", headers=admin_headers
            )
            self.assertEqual(failed_delete.status_code, 503, failed_delete.text)
        failed_detail = await self.client.get(
            f"/knowledge/files/{knowledge_id}", headers=admin_headers
        )
        self.assertEqual(failed_detail.status_code, 200, failed_detail.text)
        self.assertEqual(failed_detail.json()["status"], "failed")
        self.assertTrue(queued_path.exists())
        with patch(
            "routers.rag_router.delete_knowledge_file_vectors"
        ) as delete_vectors:
            deleted_file = await self.client.delete(
                f"/admin/knowledge/files/{knowledge_id}", headers=admin_headers
            )
            self.assertEqual(deleted_file.status_code, 200, deleted_file.text)
            delete_vectors.assert_called_once_with(self.admin_id, knowledge_id)
        async with AsyncSessionFactory() as session:
            self.assertFalse(
                await KnowledgeRepository(session).finish_processing(knowledge_id, 2, 5)
            )
        self.assertFalse(queued_path.exists())

        async with AsyncSessionFactory() as session:
            generic_task = await TaskRepository(session).create(
                user_id=self.admin_id,
                task_type="test.noop",
                target_type="test",
                target_id="1",
                payload={},
                max_attempts=2,
            )
            generic_task_id = generic_task.id
        async with AsyncSessionFactory() as session:
            self.assertIsNotNone(await TaskRepository(session).claim(generic_task_id))
        async with AsyncSessionFactory() as session:
            self.assertTrue(
                await TaskRepository(session).fail_or_retry(generic_task_id, "first")
            )
        async with AsyncSessionFactory() as session:
            self.assertIsNotNone(await TaskRepository(session).claim(generic_task_id))
        async with AsyncSessionFactory() as session:
            self.assertFalse(
                await TaskRepository(session).fail_or_retry(generic_task_id, "final")
            )
        with patch(
            "routers.task_router.send_to_queue", new=AsyncMock()
        ) as task_retry_queue:
            manual_retry = await self.client.post(
                f"/admin/tasks/{generic_task_id}/retry", headers=admin_headers
            )
            self.assertEqual(manual_retry.status_code, 200, manual_retry.text)
            self.assertEqual(manual_retry.json()["attempt_count"], 0)
            self.assertEqual(
                task_retry_queue.await_args.args[0]["task_id"], generic_task_id
            )
        canceled = await self.client.post(
            f"/admin/tasks/{generic_task_id}/cancel", headers=admin_headers
        )
        self.assertEqual(canceled.status_code, 200, canceled.text)
        self.assertEqual(canceled.json()["status"], "canceled")

        async with AsyncSessionFactory() as session:
            lease_task = await TaskRepository(session).create(
                user_id=self.admin_id,
                task_type="test.lease",
                target_type="test",
                target_id="lease",
                payload={},
                max_attempts=3,
            )
            lease_task_id = lease_task.id
        async with AsyncSessionFactory() as session:
            self.assertIsNotNone(await TaskRepository(session).claim(lease_task_id))
        async with AsyncSessionFactory() as session:
            async with session.begin():
                expired = await session.get(
                    AsyncTask, lease_task_id, with_for_update=True
                )
                expired.updated_at = datetime.now() - timedelta(minutes=3)
        async with AsyncSessionFactory() as session:
            reclaimed = await TaskRepository(session).claim(lease_task_id)
            self.assertIsNotNone(reclaimed)
            self.assertEqual(reclaimed.attempt_count, 2)

        # 登录失败次数达到阈值后，同一邮箱/IP 会被临时限制。
        for _ in range(8):
            failed_login = await self.client.post(
                "/auth/login",
                json={"email": ATTACK_EMAIL, "password": OLD_PASSWORD},
            )
            self.assertEqual(failed_login.status_code, 400, failed_login.text)
        rate_limited = await self.client.post(
            "/auth/login",
            json={"email": ATTACK_EMAIL, "password": OLD_PASSWORD},
        )
        self.assertEqual(rate_limited.status_code, 429, rate_limited.text)


if __name__ == "__main__":
    unittest.main()
