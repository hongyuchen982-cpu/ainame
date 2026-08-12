"""add naming pdf reports

Revision ID: i86f2b05c9e4
Revises: g75e1a94b8d3
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "i86f2b05c9e4"
down_revision: Union[str, None] = "g75e1a94b8d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "naming_report",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("selected_name_id", sa.Integer(), nullable=False),
        sa.Column("validation_id", sa.Integer(), nullable=True),
        sa.Column("brand_asset_id", sa.Integer(), nullable=True),
        sa.Column("client_request_id", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["brand_asset_id"], ["brand_asset.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["naming_project.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["selected_name_id"], ["selected_name.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["validation_id"], ["name_validation.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("filename"),
        sa.UniqueConstraint(
            "user_id", "client_request_id", name="uq_naming_report_user_request"
        ),
    )
    for column in (
        "user_id",
        "project_id",
        "selected_name_id",
        "validation_id",
        "brand_asset_id",
        "client_request_id",
        "name",
        "created_at",
    ):
        op.create_index(op.f(f"ix_naming_report_{column}"), "naming_report", [column])

    permission = sa.table(
        "permission",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(
        permission,
        [
            {
                "code": "reports.manage",
                "name": "管理 PDF 命名报告",
                "description": "查询和下载平台用户的 PDF 命名报告",
            }
        ],
    )
    op.execute(
        sa.text(
            "INSERT INTO role_permission (role_id, permission_id) "
            "SELECT r.id, p.id FROM role r JOIN permission p ON p.code = 'reports.manage' "
            "WHERE r.code = 'admin'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE rp FROM role_permission rp JOIN permission p ON p.id = rp.permission_id "
            "WHERE p.code = 'reports.manage'"
        )
    )
    op.execute(sa.text("DELETE FROM permission WHERE code = 'reports.manage'"))
    for column in reversed(
        (
            "user_id",
            "project_id",
            "selected_name_id",
            "validation_id",
            "brand_asset_id",
            "client_request_id",
            "name",
            "created_at",
        )
    ):
        op.drop_index(op.f(f"ix_naming_report_{column}"), table_name="naming_report")
    op.drop_table("naming_report")
