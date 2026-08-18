"""add selected_name table

Revision ID: b731a60de912
Revises: e42cdc3ac1d8
Create Date: 2026-08-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b731a60de912"
down_revision: Union[str, None] = "e42cdc3ac1d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "selected_name",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("reference", sa.Text(), nullable=False),
        sa.Column("moral", sa.Text(), nullable=False),
        sa.Column("logo_prompt", sa.Text(), nullable=False),
        sa.Column("logo_url", sa.String(length=500), nullable=False),
        sa.Column("logo_status", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("thread_id"),
    )
    op.create_index(
        op.f("ix_selected_name_user_id"),
        "selected_name",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_selected_name_user_id"), table_name="selected_name")
    op.drop_table("selected_name")
