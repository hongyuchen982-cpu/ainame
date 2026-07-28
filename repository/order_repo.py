import random
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.package import Package
from models.user_credit import UserCredit, CreditLog
from models.user_order import UserOrder


class OrderRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    def create_order_no(self) -> str:
        """
        生成订单号。
        """
        time_str = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = str(random.randint(100000, 999999))
        return f"{time_str}{random_str}"

    async def create_order(self, user_id: int, package: Package) -> UserOrder:
        """
        创建待支付订单。
        """
        async with self.session.begin():
            order = UserOrder(
                order_no=self.create_order_no(),
                user_id=user_id,
                package_id=package.id,
                amount=package.price,
                credit_count=package.credit_count,
                status="pending",
            )
            self.session.add(order)
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
        self, order_no: str, alipay_trade_no: str
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
            if order.status == "paid":
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
            )
            self.session.add(log)

            return order, True