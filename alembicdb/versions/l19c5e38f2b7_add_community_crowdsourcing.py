"""add community crowdsourcing

Revision ID: l19c5e38f2b7
Revises: k08b4d27e1a6
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "l19c5e38f2b7"
down_revision: Union[str, None] = "k08b4d27e1a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("community_poll", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("project_id", sa.Integer(), nullable=True), sa.Column("title", sa.String(160), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("category", sa.String(20), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("is_featured", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("closed_at", sa.DateTime(), nullable=True), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["project_id"], ["naming_project.id"], ondelete="SET NULL"))
    for col in ("user_id", "project_id", "category", "status", "is_featured"): op.create_index(f"ix_community_poll_{col}", "community_poll", [col])
    op.create_table("community_candidate", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("poll_id", sa.Integer(), nullable=False), sa.Column("name", sa.String(100), nullable=False), sa.Column("reference", sa.Text(), nullable=False), sa.Column("moral", sa.Text(), nullable=False), sa.Column("sort_order", sa.Integer(), nullable=False), sa.ForeignKeyConstraint(["poll_id"], ["community_poll.id"], ondelete="CASCADE")); op.create_index("ix_community_candidate_poll_id", "community_candidate", ["poll_id"])
    op.create_table("community_vote", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("poll_id", sa.Integer(), nullable=False), sa.Column("candidate_id", sa.Integer(), nullable=False), sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.ForeignKeyConstraint(["poll_id"], ["community_poll.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["candidate_id"], ["community_candidate.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"), sa.UniqueConstraint("poll_id", "user_id", name="uq_community_vote_poll_user"))
    for col in ("poll_id", "candidate_id", "user_id"): op.create_index(f"ix_community_vote_{col}", "community_vote", [col])
    op.create_table("community_comment", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("poll_id", sa.Integer(), nullable=False), sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("content", sa.String(1000), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.ForeignKeyConstraint(["poll_id"], ["community_poll.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"))
    for col in ("poll_id", "user_id", "status"): op.create_index(f"ix_community_comment_{col}", "community_comment", [col])
    op.create_table("community_report", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("reporter_id", sa.Integer(), nullable=False), sa.Column("target_type", sa.String(20), nullable=False), sa.Column("target_id", sa.Integer(), nullable=False), sa.Column("reason", sa.String(500), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("resolution", sa.String(500), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("resolved_at", sa.DateTime(), nullable=True), sa.ForeignKeyConstraint(["reporter_id"], ["user.id"], ondelete="CASCADE"), sa.UniqueConstraint("reporter_id", "target_type", "target_id", name="uq_community_reporter_target"))
    for col in ("reporter_id", "target_type", "target_id", "status"): op.create_index(f"ix_community_report_{col}", "community_report", [col])
    permission = sa.table("permission", sa.column("code", sa.String), sa.column("name", sa.String), sa.column("description", sa.String))
    op.bulk_insert(permission, [{"code": "community.moderate", "name": "社区内容管理", "description": "管理社区精选与处理内容举报"}])
    op.execute(sa.text("INSERT INTO role_permission (role_id, permission_id) SELECT r.id, p.id FROM role r JOIN permission p ON p.code='community.moderate' WHERE r.code='admin'"))


def downgrade() -> None:
    op.execute(sa.text("DELETE rp FROM role_permission rp JOIN permission p ON p.id=rp.permission_id WHERE p.code='community.moderate'")); op.execute(sa.text("DELETE FROM permission WHERE code='community.moderate'"))
    op.drop_table("community_report"); op.drop_table("community_comment"); op.drop_table("community_vote"); op.drop_table("community_candidate"); op.drop_table("community_poll")
