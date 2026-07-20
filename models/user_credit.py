from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from . import Base

class UserCredit(Base):
    __tablename__ = "user_credit"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 一个用户只有一个次数账户，所以 user_id 设置唯一
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    
    # 当前剩余次数
    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # 累计使用次数
    total_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # 累计充值次数，当前阶段还没有充值功能，先保留字段
    total_recharge: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )


class CreditLog(Base):
    __tablename__ = "credit_log"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        nullable=False,
        index=True,
    )
    
    # 变化次数：增加为正数，减少为负数
    change_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # 变化后的余额
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # 流水类型：register_gift / name_consume / recharge / refund / admin_adjust
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # 流水说明
    remark: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )