from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class NameValidation(Base):
    __tablename__ = "name_validation"
    __table_args__ = (
        UniqueConstraint("user_id", "client_request_id", name="uq_name_validation_user_request"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False
    )
    selected_name_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("selected_name.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("naming_project.id", ondelete="CASCADE"), index=True, nullable=True
    )
    client_request_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    domain_stem: Mapped[str] = mapped_column(String(63), nullable=False)
    status: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    domains: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    trademark: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    company: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    social: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    coverage: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True, nullable=False)
