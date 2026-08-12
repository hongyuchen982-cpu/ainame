from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class BrandAsset(Base):
    """A versioned brand-value package generated for one final enterprise name."""

    __tablename__ = "brand_asset"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "client_request_id", name="uq_brand_asset_user_request"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False
    )
    selected_name_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("selected_name.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    project_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("naming_project.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    validation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("name_validation.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    client_request_id: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    brief: Mapped[str] = mapped_column(Text, default="", nullable=False)
    positioning: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    slogans: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    logo_concepts: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    visual_guidelines: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    domain_matrix: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    risk_notes: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    validation_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, index=True, nullable=False
    )
