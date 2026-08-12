from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.community import CommunityCandidate, CommunityComment, CommunityPoll, CommunityReport, CommunityVote
from models.naming_project import NamingCandidate, NamingProject, NamingRound
from models.user import User


class CommunityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_poll(self, user_id: int, project_id: int, title: str, description: str, candidate_ids: list[int]):
        unique_ids = list(dict.fromkeys(candidate_ids))
        if len(unique_ids) < 2:
            raise ValueError("至少选择两个不同的候选名称")
        async with self.session.begin():
            project = await self.session.scalar(select(NamingProject).where(NamingProject.id == project_id, NamingProject.user_id == user_id))
            if not project or project.current_round < 1:
                raise LookupError("命名项目不存在或尚未生成候选名称")
            latest_round_id = await self.session.scalar(select(NamingRound.id).where(NamingRound.project_id == project.id, NamingRound.round_no == project.current_round))
            candidates = list(await self.session.scalars(select(NamingCandidate).where(NamingCandidate.round_id == latest_round_id, NamingCandidate.id.in_(unique_ids)).order_by(NamingCandidate.id)))
            if len(candidates) != len(unique_ids):
                raise ValueError("只能发布项目最新一轮中属于你的候选名称")
            poll = CommunityPoll(user_id=user_id, project_id=project.id, title=title.strip(), description=description.strip(), category=project.category)
            self.session.add(poll); await self.session.flush()
            self.session.add_all([CommunityCandidate(poll_id=poll.id, name=item.name, reference=item.reference, moral=item.moral, sort_order=index) for index, item in enumerate(candidates)])
            await self.session.flush(); return poll

    async def list_polls(self, user_id: int, *, featured: bool = False, mine: bool = False):
        async with self.session.begin():
            stmt = select(CommunityPoll, User).join(User, User.id == CommunityPoll.user_id).where(CommunityPoll.status.in_(["open", "closed"])).order_by(CommunityPoll.is_featured.desc(), CommunityPoll.id.desc())
            if featured: stmt = stmt.where(CommunityPoll.is_featured.is_(True))
            if mine: stmt = stmt.where(CommunityPoll.user_id == user_id)
            rows = list((await self.session.execute(stmt.limit(100))).all())
            return [await self._poll_data(poll, publisher, user_id, include_comments=False) for poll, publisher in rows]

    async def poll(self, poll_id: int, user_id: int, *, admin: bool = False):
        async with self.session.begin():
            stmt = select(CommunityPoll, User).join(User, User.id == CommunityPoll.user_id).where(CommunityPoll.id == poll_id)
            if not admin: stmt = stmt.where(CommunityPoll.status.in_(["open", "closed"]))
            row = (await self.session.execute(stmt)).first()
            return None if not row else await self._poll_data(*row, user_id, include_comments=True)

    async def vote(self, poll_id: int, candidate_id: int, user_id: int):
        async with self.session.begin():
            poll = await self.session.scalar(select(CommunityPoll).where(CommunityPoll.id == poll_id).with_for_update())
            if not poll or poll.status == "hidden": raise LookupError("社区投票不存在")
            if poll.status != "open": raise ValueError("投票已经结束")
            candidate = await self.session.scalar(select(CommunityCandidate).where(CommunityCandidate.id == candidate_id, CommunityCandidate.poll_id == poll.id))
            if not candidate: raise ValueError("候选名称不属于该投票")
            vote = await self.session.scalar(select(CommunityVote).where(CommunityVote.poll_id == poll.id, CommunityVote.user_id == user_id).with_for_update())
            if vote: vote.candidate_id = candidate.id
            else: self.session.add(CommunityVote(poll_id=poll.id, candidate_id=candidate.id, user_id=user_id))

    async def add_comment(self, poll_id: int, user_id: int, content: str):
        async with self.session.begin():
            poll = await self.session.scalar(select(CommunityPoll).where(CommunityPoll.id == poll_id))
            if not poll or poll.status == "hidden": raise LookupError("社区投票不存在")
            if poll.status != "open": raise ValueError("投票结束后不能继续评论")
            item = CommunityComment(poll_id=poll.id, user_id=user_id, content=content.strip())
            self.session.add(item); await self.session.flush(); return item

    async def close_poll(self, poll_id: int, user_id: int):
        async with self.session.begin():
            poll = await self.session.scalar(select(CommunityPoll).where(CommunityPoll.id == poll_id, CommunityPoll.user_id == user_id).with_for_update())
            if not poll: raise LookupError("社区投票不存在")
            if poll.status == "closed": return poll
            if poll.status != "open": raise ValueError("当前投票不能结束")
            poll.status, poll.closed_at = "closed", datetime.now(); return poll

    async def create_report(self, reporter_id: int, target_type: str, target_id: int, reason: str):
        async with self.session.begin():
            if target_type == "poll":
                target = await self.session.scalar(select(CommunityPoll).where(CommunityPoll.id == target_id, CommunityPoll.status != "hidden"))
                owner_id = target.user_id if target else None
            else:
                target = await self.session.scalar(select(CommunityComment).where(CommunityComment.id == target_id, CommunityComment.status == "visible"))
                owner_id = target.user_id if target else None
            if not target: raise LookupError("举报内容不存在")
            if owner_id == reporter_id: raise ValueError("不能举报自己发布的内容")
            existing = await self.session.scalar(select(CommunityReport).where(CommunityReport.reporter_id == reporter_id, CommunityReport.target_type == target_type, CommunityReport.target_id == target_id))
            if existing: return existing, False
            item = CommunityReport(reporter_id=reporter_id, target_type=target_type, target_id=target_id, reason=reason.strip())
            self.session.add(item); await self.session.flush(); return item, True

    async def list_reports(self, status: str | None = None):
        async with self.session.begin():
            stmt = select(CommunityReport, User).join(User, User.id == CommunityReport.reporter_id).order_by(CommunityReport.id.desc())
            if status: stmt = stmt.where(CommunityReport.status == status)
            return list((await self.session.execute(stmt.limit(200))).all())

    async def set_featured(self, poll_id: int, value: bool):
        async with self.session.begin():
            poll = await self.session.scalar(select(CommunityPoll).where(CommunityPoll.id == poll_id).with_for_update())
            if not poll: raise LookupError("社区投票不存在")
            if poll.status == "hidden" and value: raise ValueError("已隐藏内容不能设为精选")
            poll.is_featured = value; return poll

    async def moderate_report(self, report_id: int, action: str, resolution: str):
        async with self.session.begin():
            report = await self.session.scalar(select(CommunityReport).where(CommunityReport.id == report_id).with_for_update())
            if not report: raise LookupError("举报记录不存在")
            if report.status != "pending": raise ValueError("举报已经处理")
            if action == "hide":
                if report.target_type == "poll":
                    target = await self.session.scalar(select(CommunityPoll).where(CommunityPoll.id == report.target_id).with_for_update())
                    if target: target.status, target.is_featured = "hidden", False
                else:
                    target = await self.session.scalar(select(CommunityComment).where(CommunityComment.id == report.target_id).with_for_update())
                    if target: target.status = "hidden"
            report.status = "resolved" if action == "hide" else "dismissed"
            report.resolution, report.resolved_at = resolution.strip(), datetime.now(); return report

    async def _poll_data(self, poll, publisher, user_id: int, include_comments: bool):
        candidates = list(await self.session.scalars(select(CommunityCandidate).where(CommunityCandidate.poll_id == poll.id).order_by(CommunityCandidate.sort_order, CommunityCandidate.id)))
        vote_rows = list((await self.session.execute(select(CommunityVote.candidate_id, func.count(CommunityVote.id)).where(CommunityVote.poll_id == poll.id).group_by(CommunityVote.candidate_id))).all())
        vote_counts = dict(vote_rows); vote_total = sum(vote_counts.values())
        my_candidate_id = await self.session.scalar(select(CommunityVote.candidate_id).where(CommunityVote.poll_id == poll.id, CommunityVote.user_id == user_id))
        comment_count = await self.session.scalar(select(func.count(CommunityComment.id)).where(CommunityComment.poll_id == poll.id, CommunityComment.status == "visible")) or 0
        comments = []
        if include_comments:
            rows = (await self.session.execute(select(CommunityComment, User).join(User, User.id == CommunityComment.user_id).where(CommunityComment.poll_id == poll.id, CommunityComment.status == "visible").order_by(CommunityComment.id.desc()).limit(100))).all()
            comments = [{"id": item.id, "username": user.username, "content": item.content, "created_at": item.created_at} for item, user in rows]
        return {"id": poll.id, "title": poll.title, "description": poll.description, "category": poll.category, "status": poll.status, "is_featured": poll.is_featured, "publisher": publisher.username, "can_manage": poll.user_id == user_id, "vote_count": vote_total, "comment_count": comment_count, "my_candidate_id": my_candidate_id, "candidates": [{"id": item.id, "name": item.name, "reference": item.reference, "moral": item.moral, "vote_count": vote_counts.get(item.id, 0), "vote_percent": round(vote_counts.get(item.id, 0) * 100 / vote_total, 1) if vote_total else 0.0} for item in candidates], "comments": comments, "created_at": poll.created_at, "closed_at": poll.closed_at}
