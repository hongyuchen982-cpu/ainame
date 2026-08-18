"""add user profile, RBAC, devices and audit logs

Revision ID: c84f2a19d6e3
Revises: b731a60de912
Create Date: 2026-08-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c84f2a19d6e3"
down_revision: Union[str, None] = "b731a60de912"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERMISSIONS = [
    ("users.read", "查看用户"),
    ("users.update", "修改用户"),
    ("users.freeze", "冻结或解冻用户"),
    ("users.roles", "分配用户角色"),
    ("roles.manage", "管理角色权限"),
    ("audit.read", "查看管理员操作日志"),
    ("devices.manage", "管理用户登录设备"),
]


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("avatar_url", sa.String(length=500), server_default="", nullable=False),
    )
    op.add_column(
        "user",
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
    )
    op.add_column(
        "user",
        sa.Column("token_version", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "user",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    op.create_table(
        "role",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "permission",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "user_role",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["role.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )
    op.create_table(
        "role_permission",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permission.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["role.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )
    op.create_table(
        "user_device",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_name", sa.String(length=100), nullable=False),
        sa.Column("user_agent", sa.String(length=500), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("refresh_jti", sa.String(length=36), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_device_user_id"), "user_device", ["user_id"])
    op.create_table(
        "login_record",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("device_id", sa.String(length=36), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("user_agent", sa.String(length=500), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("failure_reason", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_login_record_user_id"), "login_record", ["user_id"])
    op.create_index(op.f("ix_login_record_email"), "login_record", ["email"])
    op.create_index(op.f("ix_login_record_created_at"), "login_record", ["created_at"])
    op.create_table(
        "admin_audit_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("admin_user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=100), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["admin_user_id"], ["user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_audit_log_admin_user_id"), "admin_audit_log", ["admin_user_id"])
    op.create_index(op.f("ix_admin_audit_log_action"), "admin_audit_log", ["action"])
    op.create_index(op.f("ix_admin_audit_log_created_at"), "admin_audit_log", ["created_at"])

    role_table = sa.table(
        "role",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("is_system", sa.Boolean),
    )
    permission_table = sa.table(
        "permission",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(role_table, [
        {"code": "member", "name": "普通用户", "description": "默认注册用户", "is_system": True},
        {"code": "admin", "name": "管理员", "description": "平台管理员", "is_system": True},
    ])
    op.bulk_insert(permission_table, [
        {"code": code, "name": name, "description": name}
        for code, name in PERMISSIONS
    ])
    op.execute(sa.text(
        "INSERT INTO role_permission (role_id, permission_id) "
        "SELECT r.id, p.id FROM role r CROSS JOIN permission p WHERE r.code = 'admin'"
    ))
    op.execute(sa.text(
        "INSERT INTO user_role (user_id, role_id) "
        "SELECT u.id, r.id FROM user u JOIN role r ON r.code = 'member'"
    ))


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_audit_log_created_at"), table_name="admin_audit_log")
    op.drop_index(op.f("ix_admin_audit_log_action"), table_name="admin_audit_log")
    op.drop_index(op.f("ix_admin_audit_log_admin_user_id"), table_name="admin_audit_log")
    op.drop_table("admin_audit_log")
    op.drop_index(op.f("ix_login_record_created_at"), table_name="login_record")
    op.drop_index(op.f("ix_login_record_email"), table_name="login_record")
    op.drop_index(op.f("ix_login_record_user_id"), table_name="login_record")
    op.drop_table("login_record")
    op.drop_index(op.f("ix_user_device_user_id"), table_name="user_device")
    op.drop_table("user_device")
    op.drop_table("role_permission")
    op.drop_table("user_role")
    op.drop_table("permission")
    op.drop_table("role")
    op.drop_column("user", "updated_at")
    op.drop_column("user", "created_at")
    op.drop_column("user", "token_version")
    op.drop_column("user", "status")
    op.drop_column("user", "avatar_url")
