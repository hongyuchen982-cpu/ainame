import json
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.package import Package
from models.user_credit import UserCredit, CreditLog
from models.user_order import UserOrder
from models.payment_transaction import PaymentTransaction
from models.user import User


class OrderRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    def create_order_no(self) -> str:
        """
        生成订单号。
        """
        time_str = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"{time_str}{secrets.token_hex(4)}"

    async def create_order(
        self, user_id: int, package_id: int, client_request_id: str | None = None
    ) -> tuple[UserOrder, Package]:
        """
        锁定并重新校验上架套餐，再使用当前价格和次数创建订单快照。

        套餐上下架、修改、删除与创建订单会在同一行锁上串行，避免
        用户通过已经下架或刚刚删除的套餐创建订单。
        """
        async with self.session.begin():
            # 同一用户的订单创建串行化，保证 client_request_id 并发幂等。
            user_exists = await self.session.scalar(
                select(User.id).where(User.id == user_id).with_for_update()
            )
            if user_exists is None:
                raise ValueError("用户不存在")
            if client_request_id:
                existing = await self.session.scalar(
                    select(UserOrder).where(
                        UserOrder.client_request_id == client_request_id
                    )
                )
                if existing is not None:
                    if existing.user_id != user_id:
                        raise ValueError("订单幂等键已被其他用户使用")
                    package = await self.session.get(Package, existing.package_id)
                    if package is None:
                        raise ValueError("订单关联套餐不存在")
                    return existing, package
            package = await self.session.scalar(
                select(Package)
                .where(Package.id == package_id)
                .with_for_update()
            )
            if package is None or not package.is_active:
                raise ValueError("套餐不存在或已下架")
            order = UserOrder(
                order_no=self.create_order_no(),
                user_id=user_id,
                package_id=package.id,
                package_name=package.name,
                client_request_id=client_request_id,
                amount=package.price,
                credit_count=package.credit_count,
                status="pending",
                expires_at=datetime.now() + timedelta(minutes=30),
            )
            self.session.add(order)
            await self.session.flush()
            return order, package

    async def get_for_user(self, order_no: str, user_id: int) -> UserOrder | None:
        async with self.session.begin():
            return await self.session.scalar(
                select(UserOrder).where(
                    UserOrder.order_no == order_no,
                    UserOrder.user_id == user_id,
                )
            )

    async def list_for_user(
        self, user_id: int, *, limit: int = 50, offset: int = 0
    ) -> list[UserOrder]:
        async with self.session.begin():
            return list(await self.session.scalars(
                select(UserOrder)
                .where(UserOrder.user_id == user_id)
                .order_by(UserOrder.id.desc())
                .offset(offset)
                .limit(limit)
            ))

    async def list_all(
        self, *, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[tuple[UserOrder, User]]:
        async with self.session.begin():
            statement = (
                select(UserOrder, User)
                .join(User, User.id == UserOrder.user_id)
                .order_by(UserOrder.id.desc())
                .offset(offset)
                .limit(limit)
            )
            if status:
                statement = statement.where(UserOrder.status == status)
            return list((await self.session.execute(statement)).all())

    async def list_transactions(
        self, order_id: int
    ) -> list[PaymentTransaction]:
        async with self.session.begin():
            return list(await self.session.scalars(
                select(PaymentTransaction)
                .where(PaymentTransaction.order_id == order_id)
                .order_by(PaymentTransaction.id.desc())
            ))

    async def close_pending(self, order_no: str, user_id: int | None = None) -> UserOrder:
        async with self.session.begin():
            statement = select(UserOrder).where(UserOrder.order_no == order_no)
            if user_id is not None:
                statement = statement.where(UserOrder.user_id == user_id)
            order = await self.session.scalar(statement.with_for_update())
            if order is None:
                raise LookupError("订单不存在")
            if order.status == "closed":
                return order
            if order.status != "pending":
                raise ValueError("只有待支付订单可以关闭")
            order.status = "closed"
            order.closed_at = datetime.now()
            await self.session.flush()
            return order

    async def get_by_order_no(self, order_no: str) -> UserOrder | None:
        """
        根据订单号查询订单。
        """
        async with self.session.begin():
            return await self.session.scalar(
                select(UserOrder).where(UserOrder.order_no == order_no)
            )

    async def pay_success(
        self, order_no: str, alipay_trade_no: str, detail: str = ""
    ) -> tuple[UserOrder, bool]:
        """
        支付成功后：
        1. 修改订单状态
        2. 增加用户次数
        3. 写次数流水

        返回：
        order: 订单对象
        is_first_success: 是否第一次处理成功
        如果支付宝重复通知，订单已经 paid，则不会重复加次数。
        """
        async with self.session.begin():
            order = await self.session.scalar(
                select(UserOrder)
                .where(UserOrder.order_no == order_no)
                .with_for_update()
            )
            if not order:
                raise ValueError("订单不存在")

            # 支付宝可能重复通知，如果已经支付过，直接返回，不重复加次数
            if order.status in {"paid", "refunding", "refunded"}:
                await self._upsert_transaction(
                    order=order,
                    request_no=f"payment:{order.order_no}",
                    transaction_type="payment",
                    status="success",
                    amount=order.amount,
                    provider_trade_no=alipay_trade_no,
                    detail=detail,
                )
                return order, False

            if order.status != "pending":
                raise ValueError("订单状态异常")

            # 1. 修改订单状态
            order.status = "paid"
            order.alipay_trade_no = alipay_trade_no
            order.paid_at = datetime.now()

            # 2. 查询用户次数账户
            credit = await self.session.scalar(
                select(UserCredit)
                .where(UserCredit.user_id == order.user_id)
                .with_for_update()
            )

            # 正常情况下，注册时已经创建过次数账户
            # 这里做兜底处理，防止老用户没有次数账户
            if not credit:
                credit = UserCredit(
                    user_id=order.user_id,
                    balance=0,
                    total_used=0,
                    total_recharge=0,
                )
                self.session.add(credit)
                await self.session.flush()

            # 3. 增加次数
            credit.balance += order.credit_count
            credit.total_recharge += order.credit_count

            # 4. 写次数流水
            log = CreditLog(
                user_id=order.user_id,
                change_count=order.credit_count,
                balance_after=credit.balance,
                type="recharge",
                remark=f"支付宝支付成功，充值{order.credit_count}次",
                operation_id=f"recharge:{order.order_no}",
            )
            self.session.add(log)

            await self._upsert_transaction(
                order=order,
                request_no=f"payment:{order.order_no}",
                transaction_type="payment",
                status="success",
                amount=order.amount,
                provider_trade_no=alipay_trade_no,
                detail=detail,
            )

            from repository.growth_repo import GrowthRepository
            await GrowthRepository(self.session).create_commission_in_transaction(order)

            return order, True

    async def begin_refund(
        self, order_no: str, request_no: str, reason: str
    ) -> tuple[UserOrder, PaymentTransaction, bool]:
        async with self.session.begin():
            order = await self.session.scalar(
                select(UserOrder).where(UserOrder.order_no == order_no).with_for_update()
            )
            if order is None:
                raise LookupError("订单不存在")
            existing = await self.session.scalar(
                select(PaymentTransaction).where(PaymentTransaction.request_no == request_no)
            )
            if existing is not None:
                if existing.order_id != order.id or existing.transaction_type != "refund":
                    raise ValueError("退款幂等键已被其他业务使用")
                return order, existing, existing.status == "pending"
            if order.status == "refunded":
                raise ValueError("订单已经退款")
            if order.status != "paid":
                raise ValueError("只有已支付订单可以退款")
            credit = await self.session.scalar(
                select(UserCredit).where(UserCredit.user_id == order.user_id).with_for_update()
            )
            if credit is None or credit.balance < order.credit_count:
                raise ValueError("用户剩余次数不足，无法退款")

            credit.balance -= order.credit_count
            credit.total_recharge = max(0, credit.total_recharge - order.credit_count)
            self.session.add(CreditLog(
                user_id=order.user_id,
                change_count=-order.credit_count,
                balance_after=credit.balance,
                type="refund_hold",
                remark=f"订单 {order.order_no} 退款预扣次数",
                operation_id=f"refund_hold:{request_no}",
            ))
            order.status = "refunding"
            transaction = PaymentTransaction(
                order_id=order.id,
                request_no=request_no,
                transaction_type="refund",
                status="pending",
                amount=order.amount,
                provider_trade_no=order.alipay_trade_no,
                detail=json.dumps({"reason": reason}, ensure_ascii=False),
            )
            self.session.add(transaction)
            await self.session.flush()
            return order, transaction, True

    async def complete_refund(
        self, order_no: str, request_no: str, provider_detail: str
    ) -> UserOrder:
        async with self.session.begin():
            order = await self.session.scalar(
                select(UserOrder).where(UserOrder.order_no == order_no).with_for_update()
            )
            if order is None:
                raise LookupError("订单不存在")
            transaction = await self.session.scalar(
                select(PaymentTransaction).where(
                    PaymentTransaction.request_no == request_no,
                    PaymentTransaction.order_id == order.id,
                ).with_for_update()
            )
            if transaction is None:
                raise LookupError("退款记录不存在")
            if order.status == "refunded" and transaction.status == "success":
                return order
            if order.status != "refunding" or transaction.status != "pending":
                raise ValueError("退款状态异常")
            order.status = "refunded"
            order.refund_amount = order.amount
            order.refunded_at = datetime.now()
            transaction.status = "success"
            transaction.detail = provider_detail
            from repository.growth_repo import GrowthRepository
            await GrowthRepository(self.session).reverse_commission_in_transaction(order.id)
            await self.session.flush()
            return order

    async def fail_refund(
        self, order_no: str, request_no: str, provider_detail: str
    ) -> UserOrder:
        async with self.session.begin():
            order = await self.session.scalar(
                select(UserOrder).where(UserOrder.order_no == order_no).with_for_update()
            )
            if order is None:
                raise LookupError("订单不存在")
            transaction = await self.session.scalar(
                select(PaymentTransaction)
                .where(PaymentTransaction.request_no == request_no)
                .with_for_update()
            )
            if transaction is None:
                raise LookupError("退款记录不存在")
            if transaction.status == "failed":
                return order
            credit = await self.session.scalar(
                select(UserCredit).where(UserCredit.user_id == order.user_id).with_for_update()
            )
            if credit is None:
                raise ValueError("用户次数账户不存在")
            credit.balance += order.credit_count
            credit.total_recharge += order.credit_count
            self.session.add(CreditLog(
                user_id=order.user_id,
                change_count=order.credit_count,
                balance_after=credit.balance,
                type="refund_reversed",
                remark=f"订单 {order.order_no} 退款失败，返还预扣次数",
                operation_id=f"refund_reverse:{request_no}",
            ))
            order.status = "paid"
            transaction.status = "failed"
            transaction.detail = provider_detail
            await self.session.flush()
            return order

    async def _upsert_transaction(
        self,
        *,
        order: UserOrder,
        request_no: str,
        transaction_type: str,
        status: str,
        amount,
        provider_trade_no: str,
        detail: str,
    ) -> PaymentTransaction:
        transaction = await self.session.scalar(
            select(PaymentTransaction).where(PaymentTransaction.request_no == request_no)
        )
        if transaction is None:
            transaction = PaymentTransaction(
                order_id=order.id,
                request_no=request_no,
                transaction_type=transaction_type,
                status=status,
                amount=amount,
                provider_trade_no=provider_trade_no,
                detail=detail,
            )
            self.session.add(transaction)
        else:
            transaction.status = status
            transaction.provider_trade_no = provider_trade_no
            transaction.detail = detail
        await self.session.flush()
        return transaction
