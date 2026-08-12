"""add naming projects, rounds and candidates

Revision ID: f3a7c2b91d04
Revises: c84f2a19d6e3
Create Date: 2026-08-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a7c2b91d04"
down_revision: Union[str, None] = "c84f2a19d6e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "naming_project",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False),
        sa.Column("thread_id", sa.String(length=100), nullable=True),
        sa.Column("current_round", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("thread_id"),
    )
    op.create_index(op.f("ix_naming_project_user_id"), "naming_project", ["user_id"])
    op.create_index(op.f("ix_naming_project_category"), "naming_project", ["category"])
    op.create_index(op.f("ix_naming_project_status"), "naming_project", ["status"])
    op.create_index(op.f("ix_naming_project_thread_id"), "naming_project", ["thread_id"])

    op.create_table(
        "naming_round",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("round_no", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["naming_project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "round_no", name="uq_naming_round_project_round"),
    )
    op.create_index(op.f("ix_naming_round_project_id"), "naming_round", ["project_id"])

    op.create_table(
        "naming_candidate",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("round_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("reference", sa.Text(), nullable=False),
        sa.Column("moral", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("domain_status", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["round_id"], ["naming_round.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_naming_candidate_round_id"), "naming_candidate", ["round_id"])

    op.add_column("selected_name", sa.Column("project_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_selected_name_project_id_naming_project",
        "selected_name",
        "naming_project",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        op.f("ix_selected_name_project_id"),
        "selected_name",
        ["project_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_selected_name_project_id"), table_name="selected_name")
    op.drop_constraint(
        "fk_selected_name_project_id_naming_project",
        "selected_name",
        type_="foreignkey",
    )
    op.drop_column("selected_name", "project_id")
    op.drop_index(op.f("ix_naming_candidate_round_id"), table_name="naming_candidate")
    op.drop_table("naming_candidate")
    op.drop_index(op.f("ix_naming_round_project_id"), table_name="naming_round")
    op.drop_table("naming_round")
    op.drop_index(op.f("ix_naming_project_thread_id"), table_name="naming_project")
    op.drop_index(op.f("ix_naming_project_status"), table_name="naming_project")
    op.drop_index(op.f("ix_naming_project_category"), table_name="naming_project")
    op.drop_index(op.f("ix_naming_project_user_id"), table_name="naming_project")
    op.drop_table("naming_project")
