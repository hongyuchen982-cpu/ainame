"""add knowledge file management

Revision ID: d42b7c81e5a0
Revises: c18a56d09f31
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d42b7c81e5a0"
down_revision: Union[str, None] = "c18a56d09f31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_file",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("extension", sa.String(length=10), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("processing_version", sa.Integer(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_file_user_id"), "knowledge_file", ["user_id"])
    op.create_index(op.f("ix_knowledge_file_checksum"), "knowledge_file", ["checksum"])
    op.create_index(op.f("ix_knowledge_file_status"), "knowledge_file", ["status"])

    permission = sa.table(
        "permission",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(permission, [{
        "code": "knowledge.manage",
        "name": "管理知识库",
        "description": "查询、重新处理和删除平台知识库文件",
    }])
    op.execute(sa.text(
        "INSERT INTO role_permission (role_id, permission_id) "
        "SELECT r.id, p.id FROM role r JOIN permission p ON p.code = 'knowledge.manage' "
        "WHERE r.code = 'admin'"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "DELETE rp FROM role_permission rp JOIN permission p ON p.id = rp.permission_id "
        "WHERE p.code = 'knowledge.manage'"
    ))
    op.execute(sa.text("DELETE FROM permission WHERE code = 'knowledge.manage'"))
    op.drop_index(op.f("ix_knowledge_file_status"), table_name="knowledge_file")
    op.drop_index(op.f("ix_knowledge_file_checksum"), table_name="knowledge_file")
    op.drop_index(op.f("ix_knowledge_file_user_id"), table_name="knowledge_file")
    op.drop_table("knowledge_file")
