import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.developer_platform import ApiPlan, ApiUsageLog, DeveloperAccount, DeveloperApiKey, DeveloperSubscription
from models.user import User


class DeveloperRepository:
    def __init__(self, session: AsyncSession): self.session = session

    async def create_account(self, user_id: int, **values):
        async with self.session.begin():
            existing = await self.session.scalar(select(DeveloperAccount).where(DeveloperAccount.user_id == user_id))
            if existing: raise ValueError("开发者账号已经开通")
            item = DeveloperAccount(user_id=user_id, **values); self.session.add(item); await self.session.flush(); return item

    async def account(self, user_id: int):
        async with self.session.begin(): return await self.session.scalar(select(DeveloperAccount).where(DeveloperAccount.user_id == user_id))

    async def create_key(self, user_id: int, name: str):
        raw = f"qmk_live_{secrets.token_urlsafe(32)}"; digest = hashlib.sha256(raw.encode()).hexdigest()
        async with self.session.begin():
            developer = await self._developer(user_id)
            active = await self.session.scalar(select(func.count(DeveloperApiKey.id)).where(DeveloperApiKey.developer_id == developer.id, DeveloperApiKey.status == "active"))
            if active >= 10: raise ValueError("最多保留 10 个有效 API Key")
            item = DeveloperApiKey(developer_id=developer.id, name=name.strip(), key_prefix=raw[:16], key_hash=digest)
            self.session.add(item); await self.session.flush(); return item, raw

    async def keys(self, user_id: int):
        async with self.session.begin():
            developer = await self._developer(user_id)
            return list(await self.session.scalars(select(DeveloperApiKey).where(DeveloperApiKey.developer_id == developer.id).order_by(DeveloperApiKey.id.desc())))

    async def revoke_key(self, user_id: int, key_id: int):
        async with self.session.begin():
            developer = await self._developer(user_id)
            item = await self.session.scalar(select(DeveloperApiKey).where(DeveloperApiKey.id == key_id, DeveloperApiKey.developer_id == developer.id).with_for_update())
            if not item: raise LookupError("API Key 不存在")
            if item.status != "revoked": item.status, item.revoked_at = "revoked", datetime.now()
            return item

    async def authenticate_key(self, raw: str):
        digest = hashlib.sha256(raw.encode()).hexdigest()
        async with self.session.begin():
            row = (await self.session.execute(select(DeveloperApiKey, DeveloperAccount, User).join(DeveloperAccount, DeveloperAccount.id == DeveloperApiKey.developer_id).join(User, User.id == DeveloperAccount.user_id).where(DeveloperApiKey.key_hash == digest, DeveloperApiKey.status == "active", DeveloperAccount.status == "active", User.status == "active").with_for_update())).first()
            if row: row[0].last_used_at = datetime.now()
            return row

    async def plans(self, active=True):
        async with self.session.begin():
            stmt = select(ApiPlan).order_by(ApiPlan.price, ApiPlan.id)
            if active: stmt = stmt.where(ApiPlan.is_active.is_(True))
            return list(await self.session.scalars(stmt))

    async def create_plan(self, **values):
        async with self.session.begin():
            item = ApiPlan(**values); self.session.add(item); await self.session.flush(); return item

    async def subscribe_free(self, user_id: int, plan_id: int):
        async with self.session.begin():
            developer = await self._developer(user_id)
            plan = await self.session.scalar(select(ApiPlan).where(ApiPlan.id == plan_id, ApiPlan.is_active.is_(True)).with_for_update())
            if not plan: raise LookupError("API 套餐不存在")
            if plan.price > 0: raise ValueError("付费 API 套餐请联系平台管理员开通")
            existing = await self.session.scalar(select(DeveloperSubscription.id).where(DeveloperSubscription.developer_id == developer.id, DeveloperSubscription.plan_id == plan.id))
            if existing: raise ValueError("该免费套餐已经领取")
            return await self._grant(developer.id, plan)

    async def grant(self, developer_id: int, plan_id: int):
        async with self.session.begin():
            developer = await self.session.get(DeveloperAccount, developer_id)
            plan = await self.session.get(ApiPlan, plan_id)
            if not developer or not plan: raise LookupError("开发者或套餐不存在")
            return await self._grant(developer.id, plan)

    async def subscriptions(self, developer_id: int):
        async with self.session.begin():
            return list((await self.session.execute(select(DeveloperSubscription, ApiPlan).join(ApiPlan, ApiPlan.id == DeveloperSubscription.plan_id).where(DeveloperSubscription.developer_id == developer_id).order_by(DeveloperSubscription.id.desc()))).all())

    async def reserve(self, api_key_id: int, developer_id: int, request_id: str, endpoint: str, units: int):
        async with self.session.begin():
            # 串行化同一 Key 的配额与幂等检查，避免并发重复 request_id 穿透唯一约束。
            await self.session.scalar(select(DeveloperApiKey.id).where(DeveloperApiKey.id == api_key_id).with_for_update())
            existing = await self.session.scalar(select(ApiUsageLog).where(ApiUsageLog.api_key_id == api_key_id, ApiUsageLog.request_id == request_id))
            if existing:
                if existing.endpoint != endpoint or existing.units != units:
                    raise LookupError("request_id 已被其他调用使用")
                return existing, False
            now = datetime.now()
            subscriptions = list(await self.session.scalars(select(DeveloperSubscription).where(DeveloperSubscription.developer_id == developer_id, DeveloperSubscription.status == "active", DeveloperSubscription.expires_at > now).order_by(DeveloperSubscription.expires_at, DeveloperSubscription.id).with_for_update()))
            subscription = next((item for item in subscriptions if item.quota_total - item.quota_used >= units), None)
            if not subscription: raise ValueError("API 调用额度不足")
            subscription.quota_used += units
            log = ApiUsageLog(developer_id=developer_id, api_key_id=api_key_id, subscription_id=subscription.id, request_id=request_id, endpoint=endpoint, units=units, status="processing")
            self.session.add(log); await self.session.flush(); return log, True

    async def finish(self, log_id: int, response: dict, latency: int):
        async with self.session.begin():
            log = await self.session.get(ApiUsageLog, log_id, with_for_update=True); log.status, log.response_data, log.latency_ms = "success", response, latency; return log

    async def fail(self, log_id: int, message: str, latency: int):
        async with self.session.begin():
            log = await self.session.get(ApiUsageLog, log_id, with_for_update=True)
            if log.status == "processing":
                subscription = await self.session.get(DeveloperSubscription, log.subscription_id, with_for_update=True)
                subscription.quota_used = max(0, subscription.quota_used - log.units)
            log.status, log.error_message, log.latency_ms = "failed", message[:1000], latency; return log

    async def usage(self, developer_id: int):
        async with self.session.begin(): return list(await self.session.scalars(select(ApiUsageLog).where(ApiUsageLog.developer_id == developer_id).order_by(ApiUsageLog.id.desc()).limit(200)))

    async def usage_summary(self, developer_id: int):
        async with self.session.begin():
            row = (await self.session.execute(select(func.count(ApiUsageLog.id), func.coalesce(func.sum(ApiUsageLog.units), 0), func.coalesce(func.sum(ApiUsageLog.status == "success"), 0), func.coalesce(func.sum(ApiUsageLog.status == "failed"), 0)).where(ApiUsageLog.developer_id == developer_id))).one()
            return {"calls_total": row[0], "units_total": row[1], "success_total": row[2], "failed_total": row[3]}

    async def developers(self):
        async with self.session.begin(): return list((await self.session.execute(select(DeveloperAccount, User).join(User, User.id == DeveloperAccount.user_id).order_by(DeveloperAccount.id.desc()))).all())

    async def set_status(self, developer_id: int, status: str):
        async with self.session.begin():
            item = await self.session.get(DeveloperAccount, developer_id, with_for_update=True)
            if not item: raise LookupError("开发者账号不存在")
            item.status = status
            if status == "suspended":
                keys = list(await self.session.scalars(select(DeveloperApiKey).where(DeveloperApiKey.developer_id == item.id, DeveloperApiKey.status == "active").with_for_update()))
                now = datetime.now()
                for key in keys: key.status, key.revoked_at = "revoked", now
            return item

    async def _developer(self, user_id):
        item = await self.session.scalar(select(DeveloperAccount).where(DeveloperAccount.user_id == user_id))
        if not item: raise LookupError("请先开通开发者账号")
        if item.status != "active": raise PermissionError("开发者账号已停用")
        return item

    async def _grant(self, developer_id, plan):
        now = datetime.now(); item = DeveloperSubscription(developer_id=developer_id, plan_id=plan.id, quota_total=plan.quota_calls, quota_used=0, starts_at=now, expires_at=now + timedelta(days=plan.validity_days))
        self.session.add(item); await self.session.flush(); return item
