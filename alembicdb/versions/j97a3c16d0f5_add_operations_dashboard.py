"""add operations dashboard permissions

Revision ID: j97a3c16d0f5
Revises: i86f2b05c9e4
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "j97a3c16d0f5"
down_revision: Union[str, None] = "i86f2b05c9e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    permission = sa.table(
        "permission",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(
        permission,
        [
            {"code": "dashboard.read", "name": "查看运营数据看板", "description": "查看平台核心运营数据汇总"},
            {"code": "projects.manage", "name": "管理命名项目", "description": "查询和筛选平台用户的命名项目"},
        ],
    )
    op.execute(
        sa.text(
            "INSERT INTO role_permission (role_id, permission_id) "
            "SELECT r.id, p.id FROM role r JOIN permission p "
            "ON p.code IN ('dashboard.read', 'projects.manage') WHERE r.code = 'admin'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE rp FROM role_permission rp JOIN permission p ON p.id = rp.permission_id "
            "WHERE p.code IN ('dashboard.read', 'projects.manage')"
        )
    )
    op.execute(
        sa.text("DELETE FROM permission WHERE code IN ('dashboard.read', 'projects.manage')")
    )
