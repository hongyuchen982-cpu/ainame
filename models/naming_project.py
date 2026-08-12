from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class NamingProject(Base):
    """一个用户可持续维护的命名项目。"""

    __tablename__ = "naming_project"
    __table_args__ = (
        UniqueConstraint("thread_id", name="uq_naming_project_thread_id"),
        Index("ix_naming_project_thread_id", "thread_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="draft", index=True, nullable=False
    )
    conditions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    thread_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    current_round: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class NamingRound(Base):
    """首次生成或一次反馈修改形成的候选轮次。"""

    __tablename__ = "naming_round"
    __table_args__ = (
        UniqueConstraint("project_id", "round_no", name="uq_naming_round_project_round"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("naming_project.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    round_no: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )


class NamingCandidate(Base):
    """某一轮生成的候选名称快照。"""

    __tablename__ = "naming_candidate"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    round_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("naming_round.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    reference: Mapped[str] = mapped_column(Text, default="", nullable=False)
    moral: Mapped[str] = mapped_column(Text, default="", nullable=False)
    domain: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    domain_status: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
