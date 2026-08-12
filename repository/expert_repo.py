import secrets
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.auth_models import Role, user_role
from models.expert_service import ExpertDelivery, ExpertOrder, ExpertPackage, ExpertProfile, ExpertReview, ExpertSettlement
from models.naming_project import NamingProject
from models.user import User


class ExpertRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def apply(self, user_id: int, **values) -> ExpertProfile:
        async with self.session.begin():
            item = await self.session.scalar(select(ExpertProfile).where(ExpertProfile.user_id == user_id).with_for_update())
            if item and item.status in {"pending", "approved"}:
                raise ValueError("专家申请正在审核或已经通过")
            if item:
                for key, value in values.items(): setattr(item, key, value)
                item.status, item.review_note, item.reviewed_at = "pending", "", None
            else:
                item = ExpertProfile(user_id=user_id, **values); self.session.add(item)
            await self.session.flush(); return item

    async def my_profile(self, user_id: int):
        async with self.session.begin():
            return await self.session.scalar(select(ExpertProfile).where(ExpertProfile.user_id == user_id))

    async def list_applications(self, status: str | None = None):
        async with self.session.begin():
            stmt = select(ExpertProfile, User).join(User, User.id == ExpertProfile.user_id).order_by(ExpertProfile.id.desc())
            if status: stmt = stmt.where(ExpertProfile.status == status)
            return list((await self.session.execute(stmt)).all())

    async def review_application(self, profile_id: int, status: str, note: str):
        async with self.session.begin():
            profile = await self.session.scalar(select(ExpertProfile).where(ExpertProfile.id == profile_id).with_for_update())
            if not profile: raise LookupError("专家申请不存在")
            if profile.status != "pending": raise ValueError("只有待审核申请可以处理")
            profile.status, profile.review_note, profile.reviewed_at = status, note, datetime.now()
            if status == "approved":
                role_id = await self.session.scalar(select(Role.id).where(Role.code == "expert"))
                if role_id is None:
                    raise RuntimeError("专家角色尚未初始化，请先执行数据库迁移")
                exists = await self.session.scalar(select(user_role.c.user_id).where(user_role.c.user_id == profile.user_id, user_role.c.role_id == role_id))
                if not exists: await self.session.execute(user_role.insert().values(user_id=profile.user_id, role_id=role_id))
            await self.session.flush(); return profile

    async def create_package(self, user_id: int, **values):
        async with self.session.begin():
            profile = await self.session.scalar(select(ExpertProfile).where(ExpertProfile.user_id == user_id, ExpertProfile.status == "approved"))
            if not profile: raise PermissionError("仅已认证专家可以发布套餐")
            item = ExpertPackage(expert_id=profile.id, **values); self.session.add(item); await self.session.flush(); return item, profile

    async def set_package_status(self, package_id: int, user_id: int, active: bool):
        async with self.session.begin():
            row = await self.session.execute(select(ExpertPackage, ExpertProfile).join(ExpertProfile, ExpertProfile.id == ExpertPackage.expert_id).where(ExpertPackage.id == package_id, ExpertProfile.user_id == user_id).with_for_update())
            pair = row.first()
            if not pair: raise LookupError("专家套餐不存在")
            package, profile = pair; package.is_active = active; return package, profile

    async def list_packages(self, user_id: int | None = None, public: bool = False):
        async with self.session.begin():
            stmt = select(ExpertPackage, ExpertProfile).join(ExpertProfile, ExpertProfile.id == ExpertPackage.expert_id).order_by(ExpertPackage.id.desc())
            if public: stmt = stmt.where(ExpertPackage.is_active.is_(True), ExpertProfile.status == "approved")
            if user_id is not None: stmt = stmt.where(ExpertProfile.user_id == user_id)
            return list((await self.session.execute(stmt)).all())

    async def create_order(self, user_id: int, package_id: int, project_id: int | None, requirement: str, request_id: str):
        async with self.session.begin():
            existing = await self.session.scalar(select(ExpertOrder).where(ExpertOrder.user_id == user_id, ExpertOrder.client_request_id == request_id))
            if existing: return existing, False
            row = (await self.session.execute(select(ExpertPackage, ExpertProfile).join(ExpertProfile, ExpertProfile.id == ExpertPackage.expert_id).where(ExpertPackage.id == package_id, ExpertPackage.is_active.is_(True), ExpertProfile.status == "approved").with_for_update())).first()
            if not row: raise LookupError("专家套餐不存在或已下架")
            package, profile = row
            if profile.user_id == user_id: raise ValueError("不能购买自己的专家服务")
            if project_id and not await self.session.scalar(select(NamingProject.id).where(NamingProject.id == project_id, NamingProject.user_id == user_id)):
                raise ValueError("命名项目不存在")
            item = ExpertOrder(order_no=f"EX{datetime.now():%Y%m%d%H%M%S}{secrets.token_hex(3)}", user_id=user_id, expert_id=profile.id, package_id=package.id, project_id=project_id, client_request_id=request_id, package_name=package.name, expert_name=profile.display_name, amount=package.price, requirement=requirement)
            self.session.add(item); await self.session.flush(); return item, True

    async def list_orders(self, user_id: int | None = None, expert_user_id: int | None = None, all_rows: bool = False):
        async with self.session.begin():
            stmt = select(ExpertOrder, User, ExpertDelivery, ExpertReview).join(User, User.id == ExpertOrder.user_id).outerjoin(ExpertDelivery, ExpertDelivery.order_id == ExpertOrder.id).outerjoin(ExpertReview, ExpertReview.order_id == ExpertOrder.id).order_by(ExpertOrder.id.desc())
            if user_id is not None: stmt = stmt.where(ExpertOrder.user_id == user_id)
            if expert_user_id is not None: stmt = stmt.join(ExpertProfile, ExpertProfile.id == ExpertOrder.expert_id).where(ExpertProfile.user_id == expert_user_id)
            return list((await self.session.execute(stmt)).all())

    async def accept(self, order_id: int, expert_user_id: int):
        async with self.session.begin():
            order = await self._expert_order(order_id, expert_user_id, True)
            if order.status == "accepted": return order
            if order.status != "submitted": raise ValueError("当前订单不能接单")
            order.status, order.accepted_at = "accepted", datetime.now(); return order

    async def deliver(self, order_id: int, expert_user_id: int, **values):
        async with self.session.begin():
            order = await self._expert_order(order_id, expert_user_id, True)
            if order.status not in {"accepted", "delivered"}: raise ValueError("请先接单后再交付")
            delivery = await self.session.scalar(select(ExpertDelivery).where(ExpertDelivery.order_id == order.id))
            if delivery:
                for key, value in values.items(): setattr(delivery, key, value)
            else:
                delivery = ExpertDelivery(order_id=order.id, **values); self.session.add(delivery)
            order.status, order.delivered_at = "delivered", datetime.now(); await self.session.flush(); return order, delivery

    async def review_order(self, order_id: int, user_id: int, rating: int, content: str):
        async with self.session.begin():
            order = await self.session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.user_id == user_id).with_for_update())
            if not order: raise LookupError("专家订单不存在")
            if order.status != "delivered": raise ValueError("只有已交付订单可以评价")
            if await self.session.scalar(select(ExpertReview.id).where(ExpertReview.order_id == order.id)): raise ValueError("订单已经评价")
            review = ExpertReview(order_id=order.id, user_id=user_id, expert_id=order.expert_id, rating=rating, content=content); self.session.add(review)
            order.status, order.completed_at = "completed", datetime.now()
            profile = await self.session.scalar(select(ExpertProfile).where(ExpertProfile.id == order.expert_id).with_for_update())
            profile.rating_average = ((Decimal(profile.rating_average) * profile.rating_count + Decimal(rating)) / Decimal(profile.rating_count + 1)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP); profile.rating_count += 1
            fee = (Decimal(order.amount) * Decimal("0.10")).quantize(Decimal("0.01")); settlement = ExpertSettlement(order_id=order.id, expert_id=order.expert_id, gross_amount=order.amount, platform_fee=fee, net_amount=Decimal(order.amount) - fee); self.session.add(settlement)
            await self.session.flush(); return order, review, settlement

    async def list_settlements(self, expert_user_id: int | None = None):
        async with self.session.begin():
            stmt = select(ExpertSettlement, ExpertOrder, ExpertProfile).join(ExpertOrder, ExpertOrder.id == ExpertSettlement.order_id).join(ExpertProfile, ExpertProfile.id == ExpertSettlement.expert_id).order_by(ExpertSettlement.id.desc())
            if expert_user_id is not None: stmt = stmt.where(ExpertProfile.user_id == expert_user_id)
            return list((await self.session.execute(stmt)).all())

    async def settle(self, settlement_id: int):
        async with self.session.begin():
            item = await self.session.scalar(select(ExpertSettlement).where(ExpertSettlement.id == settlement_id).with_for_update())
            if not item: raise LookupError("结算记录不存在")
            if item.status == "settled": return item
            if item.status != "pending": raise ValueError("结算状态异常")
            item.status, item.settled_at = "settled", datetime.now(); return item

    async def _expert_order(self, order_id: int, user_id: int, lock: bool = False):
        stmt = select(ExpertOrder).join(ExpertProfile, ExpertProfile.id == ExpertOrder.expert_id).where(ExpertOrder.id == order_id, ExpertProfile.user_id == user_id)
        if lock: stmt = stmt.with_for_update()
        order = await self.session.scalar(stmt)
        if not order: raise LookupError("专家订单不存在")
        return order
