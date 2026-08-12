"""enhance credit entitlements

Revision ID: a91d4e6f20c8
Revises: f3a7c2b91d04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a91d4e6f20c8"
down_revision: Union[str, None] = "f3a7c2b91d04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("credit_log", sa.Column("operation_id", sa.String(length=100), nullable=True))
    op.create_index(
        op.f("ix_credit_log_operation_id"),
        "credit_log",
        ["operation_id"],
        unique=True,
    )

    permission = sa.table(
        "permission",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(permission, [{
        "code": "credits.manage",
        "name": "管理用户次数",
        "description": "查询和调整用户次数权益",
    }])
    op.execute(sa.text(
        "INSERT INTO role_permission (role_id, permission_id) "
        "SELECT r.id, p.id FROM role r JOIN permission p ON p.code = 'credits.manage' "
        "WHERE r.code = 'admin'"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "DELETE rp FROM role_permission rp "
        "JOIN permission p ON p.id = rp.permission_id "
        "WHERE p.code = 'credits.manage'"
    ))
    op.execute(sa.text("DELETE FROM permission WHERE code = 'credits.manage'"))
    op.drop_index(op.f("ix_credit_log_operation_id"), table_name="credit_log")
    op.drop_column("credit_log", "operation_id")
