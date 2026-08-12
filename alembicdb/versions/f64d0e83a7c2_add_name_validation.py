"""add name validation

Revision ID: f64d0e83a7c2
Revises: e53c9d72f6b1
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f64d0e83a7c2"
down_revision: Union[str, None] = "e53c9d72f6b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "name_validation",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("selected_name_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("client_request_id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("domain_stem", sa.String(length=63), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("domains", sa.JSON(), nullable=False),
        sa.Column("trademark", sa.JSON(), nullable=False),
        sa.Column("company", sa.JSON(), nullable=False),
        sa.Column("social", sa.JSON(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("coverage", sa.Integer(), nullable=False),
        sa.Column("risk_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["naming_project.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["selected_name_id"], ["selected_name.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "client_request_id", name="uq_name_validation_user_request"),
    )
    op.create_index(op.f("ix_name_validation_user_id"), "name_validation", ["user_id"])
    op.create_index(op.f("ix_name_validation_selected_name_id"), "name_validation", ["selected_name_id"])
    op.create_index(op.f("ix_name_validation_project_id"), "name_validation", ["project_id"])
    op.create_index(op.f("ix_name_validation_client_request_id"), "name_validation", ["client_request_id"])
    op.create_index(op.f("ix_name_validation_name"), "name_validation", ["name"])
    op.create_index(op.f("ix_name_validation_status"), "name_validation", ["status"])
    op.create_index(op.f("ix_name_validation_risk_level"), "name_validation", ["risk_level"])
    op.create_index(op.f("ix_name_validation_created_at"), "name_validation", ["created_at"])

    permission = sa.table(
        "permission",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(permission, [{
        "code": "validations.manage",
        "name": "管理名称校验",
        "description": "查询平台名称校验记录和风险结果",
    }])
    op.execute(sa.text(
        "INSERT INTO role_permission (role_id, permission_id) "
        "SELECT r.id, p.id FROM role r JOIN permission p ON p.code = 'validations.manage' "
        "WHERE r.code = 'admin'"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "DELETE rp FROM role_permission rp JOIN permission p ON p.id = rp.permission_id "
        "WHERE p.code = 'validations.manage'"
    ))
    op.execute(sa.text("DELETE FROM permission WHERE code = 'validations.manage'"))
    op.drop_index(op.f("ix_name_validation_created_at"), table_name="name_validation")
    op.drop_index(op.f("ix_name_validation_risk_level"), table_name="name_validation")
    op.drop_index(op.f("ix_name_validation_status"), table_name="name_validation")
    op.drop_index(op.f("ix_name_validation_name"), table_name="name_validation")
    op.drop_index(op.f("ix_name_validation_client_request_id"), table_name="name_validation")
    op.drop_index(op.f("ix_name_validation_project_id"), table_name="name_validation")
    op.drop_index(op.f("ix_name_validation_selected_name_id"), table_name="name_validation")
    op.drop_index(op.f("ix_name_validation_user_id"), table_name="name_validation")
    op.drop_table("name_validation")
