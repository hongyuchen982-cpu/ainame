from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class SelectedName(Base):
    """用户从一次命名会话中确认的最终名称。"""

    __tablename__ = "selected_name"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("naming_project.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=True,
    )
    thread_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    reference: Mapped[str] = mapped_column(Text, default="", nullable=False)
    moral: Mapped[str] = mapped_column(Text, default="", nullable=False)
    logo_prompt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    logo_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    logo_status: Mapped[str] = mapped_column(
        String(100),
        default="not_generated",
        nullable=False,
    )
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
