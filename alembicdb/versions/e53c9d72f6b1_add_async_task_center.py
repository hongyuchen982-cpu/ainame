"""add async task center

Revision ID: e53c9d72f6b1
Revises: d42b7c81e5a0
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e53c9d72f6b1"
down_revision: Union[str, None] = "d42b7c81e5a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "async_task",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_async_task_user_id"), "async_task", ["user_id"])
    op.create_index(op.f("ix_async_task_task_type"), "async_task", ["task_type"])
    op.create_index(op.f("ix_async_task_target_id"), "async_task", ["target_id"])
    op.create_index(op.f("ix_async_task_status"), "async_task", ["status"])

    permission = sa.table(
        "permission",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(permission, [{
        "code": "tasks.manage",
        "name": "管理异步任务",
        "description": "查询、重试和取消平台异步任务",
    }])
    op.execute(sa.text(
        "INSERT INTO role_permission (role_id, permission_id) "
        "SELECT r.id, p.id FROM role r JOIN permission p ON p.code = 'tasks.manage' "
        "WHERE r.code = 'admin'"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "DELETE rp FROM role_permission rp JOIN permission p ON p.id = rp.permission_id "
        "WHERE p.code = 'tasks.manage'"
    ))
    op.execute(sa.text("DELETE FROM permission WHERE code = 'tasks.manage'"))
    op.drop_index(op.f("ix_async_task_status"), table_name="async_task")
    op.drop_index(op.f("ix_async_task_target_id"), table_name="async_task")
    op.drop_index(op.f("ix_async_task_task_type"), table_name="async_task")
    op.drop_index(op.f("ix_async_task_user_id"), table_name="async_task")
    op.drop_table("async_task")
