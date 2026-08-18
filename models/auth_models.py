from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Table, Column, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


user_role = Table(
    "user_role",
    Base.metadata,
    Column("user_id", ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
)

role_permission = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Permission(Base):
    __tablename__ = "permission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)


class UserDevice(Base):
    __tablename__ = "user_device"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False
    )
    device_name: Mapped[str] = mapped_column(String(100), default="未知设备", nullable=False)
    user_agent: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    ip_address: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    refresh_jti: Mapped[str] = mapped_column(String(36), default="", nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class LoginRecord(Base):
    __tablename__ = "login_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="SET NULL"), index=True, nullable=True
    )
    email: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    device_id: Mapped[str] = mapped_column(String(36), default="", nullable=False)
    ip_address: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    user_agent: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failure_reason: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True, nullable=False)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="", nullable=False)
    ip_address: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True, nullable=False)
