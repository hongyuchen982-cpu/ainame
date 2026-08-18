from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class NamingReport(Base):
    __tablename__ = "naming_report"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "client_request_id", name="uq_naming_report_user_request"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("naming_project.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    selected_name_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("selected_name.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    validation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("name_validation.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    brand_asset_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("brand_asset.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    client_request_id: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, index=True, nullable=False
    )
