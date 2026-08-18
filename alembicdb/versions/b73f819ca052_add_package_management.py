"""add package management

Revision ID: b73f819ca052
Revises: a91d4e6f20c8
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b73f819ca052"
down_revision: Union[str, None] = "a91d4e6f20c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("package", sa.Column("description", sa.String(length=255), server_default="", nullable=False))
    op.add_column("package", sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False))
    op.add_column("package", sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.create_index(op.f("ix_package_sort_order"), "package", ["sort_order"])
    op.alter_column("package", "description", server_default=None)
    op.alter_column("package", "sort_order", server_default=None)
    op.alter_column("package", "updated_at", server_default=None)

    permission = sa.table(
        "permission",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(permission, [{
        "code": "packages.manage",
        "name": "管理套餐",
        "description": "新增、修改、上下架、排序和删除套餐",
    }])
    op.execute(sa.text(
        "INSERT INTO role_permission (role_id, permission_id) "
        "SELECT r.id, p.id FROM role r JOIN permission p ON p.code = 'packages.manage' "
        "WHERE r.code = 'admin'"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "DELETE rp FROM role_permission rp JOIN permission p ON p.id = rp.permission_id "
        "WHERE p.code = 'packages.manage'"
    ))
    op.execute(sa.text("DELETE FROM permission WHERE code = 'packages.manage'"))
    op.drop_index(op.f("ix_package_sort_order"), table_name="package")
    op.drop_column("package", "updated_at")
    op.drop_column("package", "sort_order")
    op.drop_column("package", "description")
