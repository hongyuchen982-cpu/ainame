from datetime import datetime
from decimal import Decimal
from sqlalchemy import Integer, String, DateTime, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from . import Base

class Package(Base):
    __tablename__ = "package"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, 
    autoincrement=True)
    # 套餐名称
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 套餐价格
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # 前台展示说明
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    # 套餐包含的起名次数
    credit_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # 是否上架
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, 
    nullable=False)
    # 数字越小越靠前
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
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
