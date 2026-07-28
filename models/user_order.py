from datetime import datetime
from decimal import Decimal
from sqlalchemy import Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from . import Base

class UserOrder(Base):
    __tablename__ = "user_order"
    id: Mapped[int] = mapped_column(Integer, primary_key=True,
autoincrement=True)
    # 系统内部订单号
    order_no: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    # 用户 id
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        index=True,
        nullable=False,
    )
    # 套餐 id
    package_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("package.id"),
        nullable=False,
    )
    # 支付金额
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # 购买次数
    credit_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # 订单状态：pending 待支付，paid 已支付，closed 已关闭
    status: Mapped[str] = mapped_column(String(20), default="pending",
nullable=False)
    # 支付宝交易号
    alipay_trade_no: Mapped[str] = mapped_column(String(100), default="",
nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
