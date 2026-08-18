"""add brand value assets

Revision ID: g75e1a94b8d3
Revises: f64d0e83a7c2
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g75e1a94b8d3"
down_revision: Union[str, None] = "f64d0e83a7c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "brand_asset",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("selected_name_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("validation_id", sa.Integer(), nullable=True),
        sa.Column("client_request_id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("brief", sa.Text(), nullable=False),
        sa.Column("positioning", sa.JSON(), nullable=False),
        sa.Column("slogans", sa.JSON(), nullable=False),
        sa.Column("logo_concepts", sa.JSON(), nullable=False),
        sa.Column("visual_guidelines", sa.JSON(), nullable=False),
        sa.Column("domain_matrix", sa.JSON(), nullable=False),
        sa.Column("risk_notes", sa.JSON(), nullable=False),
        sa.Column("validation_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
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
        sa.UniqueConstraint(
            "user_id", "client_request_id", name="uq_brand_asset_user_request"
        ),
    )
    for column in (
        "user_id",
        "selected_name_id",
        "project_id",
        "validation_id",
        "client_request_id",
        "name",
        "created_at",
    ):
        op.create_index(op.f(f"ix_brand_asset_{column}"), "brand_asset", [column])

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
                "code": "brand_assets.manage",
                "name": "管理品牌价值资产",
                "description": "查询平台用户生成的品牌价值资产",
            }
        ],
    )
    op.execute(
        sa.text(
            "INSERT INTO role_permission (role_id, permission_id) "
            "SELECT r.id, p.id FROM role r JOIN permission p ON p.code = 'brand_assets.manage' "
            "WHERE r.code = 'admin'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE rp FROM role_permission rp JOIN permission p ON p.id = rp.permission_id "
            "WHERE p.code = 'brand_assets.manage'"
        )
    )
    op.execute(sa.text("DELETE FROM permission WHERE code = 'brand_assets.manage'"))
    for column in reversed(
        (
            "user_id",
            "selected_name_id",
            "project_id",
            "validation_id",
            "client_request_id",
            "name",
            "created_at",
        )
    ):
        op.drop_index(op.f(f"ix_brand_asset_{column}"), table_name="brand_asset")
    op.drop_table("brand_asset")
