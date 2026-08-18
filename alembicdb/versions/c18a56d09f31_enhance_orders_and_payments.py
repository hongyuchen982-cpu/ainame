"""enhance orders and payments

Revision ID: c18a56d09f31
Revises: b73f819ca052
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c18a56d09f31"
down_revision: Union[str, None] = "b73f819ca052"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_order", sa.Column("package_name", sa.String(length=100), server_default="", nullable=False))
    op.add_column("user_order", sa.Column("client_request_id", sa.String(length=100), nullable=True))
    op.add_column("user_order", sa.Column("closed_at", sa.DateTime(), nullable=True))
    op.add_column("user_order", sa.Column("refunded_at", sa.DateTime(), nullable=True))
    op.add_column("user_order", sa.Column("refund_amount", sa.Numeric(10, 2), server_default="0.00", nullable=False))
    op.add_column("user_order", sa.Column("expires_at", sa.DateTime(), nullable=True))
    op.execute(sa.text(
        "UPDATE user_order o JOIN package p ON p.id = o.package_id "
        "SET o.package_name = p.name"
    ))
    op.alter_column("user_order", "package_name", server_default=None)
    op.alter_column("user_order", "refund_amount", server_default=None)
    op.create_index(op.f("ix_user_order_client_request_id"), "user_order", ["client_request_id"], unique=True)

    op.create_table(
        "payment_transaction",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("request_no", sa.String(length=100), nullable=False),
        sa.Column("transaction_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("provider_trade_no", sa.String(length=100), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["user_order.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_transaction_order_id"), "payment_transaction", ["order_id"])
    op.create_index(op.f("ix_payment_transaction_request_no"), "payment_transaction", ["request_no"], unique=True)
    op.create_index(op.f("ix_payment_transaction_status"), "payment_transaction", ["status"])
    op.create_index(op.f("ix_payment_transaction_transaction_type"), "payment_transaction", ["transaction_type"])

    permission = sa.table("permission", sa.column("code", sa.String), sa.column("name", sa.String), sa.column("description", sa.String))
    op.bulk_insert(permission, [
        {"code": "orders.manage", "name": "管理订单", "description": "查询和关闭平台订单"},
        {"code": "orders.refund", "name": "订单退款", "description": "发起并处理支付宝退款"},
    ])
    op.execute(sa.text(
        "INSERT INTO role_permission (role_id, permission_id) "
        "SELECT r.id, p.id FROM role r JOIN permission p ON p.code IN ('orders.manage','orders.refund') "
        "WHERE r.code = 'admin'"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "DELETE rp FROM role_permission rp JOIN permission p ON p.id = rp.permission_id "
        "WHERE p.code IN ('orders.manage','orders.refund')"
    ))
    op.execute(sa.text("DELETE FROM permission WHERE code IN ('orders.manage','orders.refund')"))
    op.drop_index(op.f("ix_payment_transaction_transaction_type"), table_name="payment_transaction")
    op.drop_index(op.f("ix_payment_transaction_status"), table_name="payment_transaction")
    op.drop_index(op.f("ix_payment_transaction_request_no"), table_name="payment_transaction")
    op.drop_index(op.f("ix_payment_transaction_order_id"), table_name="payment_transaction")
    op.drop_table("payment_transaction")
    op.drop_index(op.f("ix_user_order_client_request_id"), table_name="user_order")
    op.drop_column("user_order", "expires_at")
    op.drop_column("user_order", "refund_amount")
    op.drop_column("user_order", "refunded_at")
    op.drop_column("user_order", "closed_at")
    op.drop_column("user_order", "client_request_id")
    op.drop_column("user_order", "package_name")
