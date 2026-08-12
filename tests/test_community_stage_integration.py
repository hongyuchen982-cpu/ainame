"""社区众包阶段的真实 MySQL 集成测试。"""

import unittest

import httpx
from sqlalchemy import delete, select

from core.redistools import redis_client
from main import app
from models import AsyncSessionFactory, engine
from models.auth_models import AdminAuditLog, Role, user_role
from models.community import CommunityCandidate, CommunityComment, CommunityPoll, CommunityReport, CommunityVote
from models.naming_project import NamingCandidate, NamingProject, NamingRound
from models.user import User


PUBLISHER_EMAIL = "__community_stage_publisher__@example.com"
VOTER_EMAIL = "__community_stage_voter__@example.com"
ADMIN_EMAIL = "__community_stage_admin__@example.com"
PASSWORD = "TestPass123!"


class CommunityStageIntegrationTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await self.cleanup()
        async with AsyncSessionFactory() as session:
            async with session.begin():
                publisher = User(email=PUBLISHER_EMAIL, username="社区发布者", password=PASSWORD)
                voter = User(email=VOTER_EMAIL, username="社区投票者", password=PASSWORD)
                admin = User(email=ADMIN_EMAIL, username="社区管理员", password=PASSWORD)
                session.add_all([publisher, voter, admin]); await session.flush()
                roles = {role.code: role.id for role in await session.scalars(select(Role).where(Role.code.in_(["member", "admin"])))}
                await session.execute(user_role.insert(), [{"user_id": publisher.id, "role_id": roles["member"]}, {"user_id": voter.id, "role_id": roles["member"]}, {"user_id": admin.id, "role_id": roles["member"]}, {"user_id": admin.id, "role_id": roles["admin"]}])
                project = NamingProject(user_id=publisher.id, title="社区企业命名测试", category="企业名", status="generated", conditions={}, thread_id="__community_stage_thread__", current_round=1)
                session.add(project); await session.flush()
                naming_round = NamingRound(project_id=project.id, round_no=1, feedback="")
                session.add(naming_round); await session.flush()
                candidates = [NamingCandidate(round_id=naming_round.id, name=name, reference=f"{name}出处", moral=f"{name}寓意", domain="", domain_status="") for name in ("星序", "云章", "澄远")]
                session.add_all(candidates); await session.flush()
                self.project_id, self.candidate_ids = project.id, [item.id for item in candidates]
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")

    async def asyncTearDown(self):
        await self.client.aclose(); await self.cleanup(); await redis_client.aclose(); await engine.dispose()

    async def cleanup(self):
        async with AsyncSessionFactory() as session:
            async with session.begin():
                ids = list(await session.scalars(select(User.id).where(User.email.in_([PUBLISHER_EMAIL, VOTER_EMAIL, ADMIN_EMAIL]))))
                if not ids: return
                poll_ids = list(await session.scalars(select(CommunityPoll.id).where(CommunityPoll.user_id.in_(ids))))
                await session.execute(delete(CommunityReport).where((CommunityReport.reporter_id.in_(ids)) | (CommunityReport.target_id.in_(poll_ids) & (CommunityReport.target_type == "poll"))))
                await session.execute(delete(CommunityVote).where((CommunityVote.user_id.in_(ids)) | CommunityVote.poll_id.in_(poll_ids)))
                await session.execute(delete(CommunityComment).where((CommunityComment.user_id.in_(ids)) | CommunityComment.poll_id.in_(poll_ids)))
                await session.execute(delete(CommunityCandidate).where(CommunityCandidate.poll_id.in_(poll_ids)))
                await session.execute(delete(CommunityPoll).where(CommunityPoll.id.in_(poll_ids)))
                project_ids = list(await session.scalars(select(NamingProject.id).where(NamingProject.user_id.in_(ids), NamingProject.thread_id == "__community_stage_thread__")))
                round_ids = list(await session.scalars(select(NamingRound.id).where(NamingRound.project_id.in_(project_ids))))
                await session.execute(delete(NamingCandidate).where(NamingCandidate.round_id.in_(round_ids)))
                await session.execute(delete(NamingRound).where(NamingRound.id.in_(round_ids)))
                await session.execute(delete(NamingProject).where(NamingProject.id.in_(project_ids)))
                await session.execute(delete(AdminAuditLog).where(AdminAuditLog.admin_user_id.in_(ids)))
                await session.execute(delete(user_role).where(user_role.c.user_id.in_(ids)))
                await session.execute(delete(User).where(User.id.in_(ids)))

    async def login(self, email):
        response = await self.client.post("/auth/login", json={"email": email, "password": PASSWORD})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    async def test_complete_community_flow(self):
        publisher = await self.login(PUBLISHER_EMAIL); voter = await self.login(VOTER_EMAIL); admin = await self.login(ADMIN_EMAIL)
        self.assertEqual((await self.client.get("/admin/community/reports", headers=voter)).status_code, 403)
        invalid = await self.client.post("/community/polls", headers=voter, json={"project_id": self.project_id, "title": "越权发布测试", "description": "", "candidate_ids": self.candidate_ids[:2]})
        self.assertEqual(invalid.status_code, 404)
        created = await self.client.post("/community/polls", headers=publisher, json={"project_id": self.project_id, "title": "哪个企业名称更适合长期品牌发展？", "description": "希望兼顾科技感、中文语义和传播辨识度。", "candidate_ids": self.candidate_ids})
        self.assertEqual(created.status_code, 200, created.text)
        poll = created.json(); poll_id = poll["id"]
        self.assertEqual(len(poll["candidates"]), 3)
        candidate_a, candidate_b = poll["candidates"][0]["id"], poll["candidates"][1]["id"]
        voted = await self.client.post(f"/community/polls/{poll_id}/vote", headers=voter, json={"candidate_id": candidate_a})
        self.assertEqual(voted.status_code, 200, voted.text); self.assertEqual(voted.json()["vote_count"], 1)
        changed = await self.client.post(f"/community/polls/{poll_id}/vote", headers=voter, json={"candidate_id": candidate_b})
        self.assertEqual(changed.json()["vote_count"], 1); self.assertEqual(changed.json()["my_candidate_id"], candidate_b)
        commented = await self.client.post(f"/community/polls/{poll_id}/comments", headers=voter, json={"content": "我更喜欢云章，读音舒展，也有文化延展空间。"})
        self.assertEqual(commented.status_code, 200, commented.text)
        comment_id = commented.json()["comments"][0]["id"]
        self.assertEqual((await self.client.post("/community/reports", headers=voter, json={"target_type": "comment", "target_id": comment_id, "reason": "不能举报自己的评论"})).status_code, 400)
        comment_report = await self.client.post("/community/reports", headers=publisher, json={"target_type": "comment", "target_id": comment_id, "reason": "测试评论举报与隐藏流程。"})
        self.assertEqual(comment_report.status_code, 200, comment_report.text)
        hidden_comment = await self.client.post(f"/admin/community/reports/{comment_report.json()['id']}/moderate", headers=admin, json={"action": "hide", "resolution": "测试确认违规并隐藏评论"})
        self.assertEqual(hidden_comment.status_code, 200, hidden_comment.text)
        after_hide = await self.client.get(f"/community/polls/{poll_id}", headers=publisher)
        self.assertFalse(any(item["id"] == comment_id for item in after_hide.json()["comments"]))
        report_payload = {"target_type": "poll", "target_id": poll_id, "reason": "测试举报流程，请管理员核查内容。"}
        report = await self.client.post("/community/reports", headers=voter, json=report_payload)
        duplicate = await self.client.post("/community/reports", headers=voter, json=report_payload)
        self.assertEqual(report.status_code, 200, report.text); self.assertEqual(report.json()["id"], duplicate.json()["id"])
        featured = await self.client.post(f"/admin/community/polls/{poll_id}/featured", headers=admin, json={"is_featured": True})
        self.assertEqual(featured.status_code, 200, featured.text); self.assertTrue(featured.json()["is_featured"])
        featured_list = await self.client.get("/community/polls?featured=true", headers=voter)
        self.assertTrue(any(item["id"] == poll_id for item in featured_list.json()))
        dismissed = await self.client.post(f"/admin/community/reports/{report.json()['id']}/moderate", headers=admin, json={"action": "dismiss", "resolution": "核查后未发现违规"})
        self.assertEqual(dismissed.status_code, 200, dismissed.text); self.assertEqual(dismissed.json()["status"], "dismissed")
        closed = await self.client.post(f"/community/polls/{poll_id}/close", headers=publisher)
        self.assertEqual(closed.status_code, 200, closed.text); self.assertEqual(closed.json()["status"], "closed")
        self.assertEqual((await self.client.post(f"/community/polls/{poll_id}/vote", headers=voter, json={"candidate_id": candidate_a})).status_code, 400)
        self.assertEqual((await self.client.post(f"/community/polls/{poll_id}/close", headers=voter)).status_code, 404)


if __name__ == "__main__":
    unittest.main()
