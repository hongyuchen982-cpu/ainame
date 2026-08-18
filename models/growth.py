from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class GrowthCampaign(Base):
    __tablename__ = "growth_campaign"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    inviter_reward: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invitee_reward: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)


class PromotionCode(Base):
    __tablename__ = "promotion_code"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)


class ReferralRelation(Base):
    __tablename__ = "referral_relation"
    __table_args__ = (UniqueConstraint("invitee_id", name="uq_referral_invitee"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inviter_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="RESTRICT"), index=True, nullable=False)
    invitee_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False)
    promotion_code_id: Mapped[int] = mapped_column(Integer, ForeignKey("promotion_code.id", ondelete="RESTRICT"), nullable=False)
    campaign_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("growth_campaign.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)


class ReferralReward(Base):
    __tablename__ = "referral_reward"
    __table_args__ = (UniqueConstraint("relation_id", "beneficiary_type", name="uq_referral_reward_relation_type"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    relation_id: Mapped[int] = mapped_column(Integer, ForeignKey("referral_relation.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False)
    beneficiary_type: Mapped[str] = mapped_column(String(20), nullable=False)
    credit_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="granted", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)


class ReferralCommission(Base):
    __tablename__ = "referral_commission"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    relation_id: Mapped[int] = mapped_column(Integer, ForeignKey("referral_relation.id", ondelete="RESTRICT"), index=True, nullable=False)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_order.id", ondelete="RESTRICT"), unique=True, index=True, nullable=False)
    inviter_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="RESTRICT"), index=True, nullable=False)
    order_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="available", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
