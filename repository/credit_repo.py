from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.user_credit import UserCredit, CreditLog
from models.user import User

class CreditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_register_credit(self, user_id: int, gift_count: int = 3) -> UserCredit:
        """
        注册成功后，给用户创建次数账户，并赠送起名次数。
        """
        async with self.session.begin():
            return await self.create_register_credit_in_transaction(user_id, gift_count)

    async def create_register_credit_in_transaction(
        self, user_id: int, gift_count: int = 3
    ) -> UserCredit:
        """在调用方已经开启的事务中创建次数账户和赠送流水。"""
        credit = UserCredit(
            user_id=user_id,
            balance=gift_count,
            total_used=0,
            total_recharge=0,
        )
        self.session.add(credit)
        self.session.add(CreditLog(
            user_id=user_id,
            change_count=gift_count,
            balance_after=gift_count,
            type="register_gift",
            remark=f"注册赠送{gift_count}次起名机会",
        ))
        await self.session.flush()
        return credit

    async def get_balance(self, user_id: int) -> int:
        """
        查询用户剩余次数。
        如果没有次数账户，返回 0。
        """
        async with self.session.begin():
            credit = await self.session.scalar(
                select(UserCredit).where(UserCredit.user_id == user_id)
            )
            if not credit:
                return 0
            return credit.balance

    async def consume_name_credit(self, user_id: int) -> int:
        """
        起名成功后扣除 1 次。
        返回扣除后的剩余次数。
        """
        async with self.session.begin():
            return await self.consume_name_credit_in_transaction(user_id)

    async def consume_name_credit_in_transaction(
        self, user_id: int, operation_id: str | None = None
    ) -> int:
        credit = await self.session.scalar(
            select(UserCredit)
            .where(UserCredit.user_id == user_id)
            .with_for_update()
        )
        if not credit:
            raise ValueError("用户次数账户不存在")

        if operation_id:
            existing = await self.session.scalar(
                select(CreditLog).where(CreditLog.operation_id == operation_id)
            )
            if existing is not None:
                return existing.balance_after
        if credit.balance <= 0:
            raise ValueError("起名次数不足")

        credit.balance -= 1
        credit.total_used += 1
        self.session.add(CreditLog(
            user_id=user_id,
            change_count=-1,
            balance_after=credit.balance,
            type="name_consume",
            remark="AI起名消耗1次",
            operation_id=operation_id,
        ))
        await self.session.flush()
        return credit.balance

    async def get_account(self, user_id: int) -> UserCredit | None:
        async with self.session.begin():
            return await self.session.scalar(
                select(UserCredit).where(UserCredit.user_id == user_id)
            )

    async def list_logs(
        self, user_id: int, *, limit: int = 50, offset: int = 0
    ) -> list[CreditLog]:
        async with self.session.begin():
            return list(await self.session.scalars(
                select(CreditLog)
                .where(CreditLog.user_id == user_id)
                .order_by(CreditLog.id.desc())
                .offset(offset)
                .limit(limit)
            ))

    async def refund_name_credit(
        self, user_id: int, operation_id: str, remark: str = "起名失败返还"
    ) -> int:
        async with self.session.begin():
            credit = await self.session.scalar(
                select(UserCredit)
                .where(UserCredit.user_id == user_id)
                .with_for_update()
            )
            if credit is None:
                raise ValueError("用户次数账户不存在")
            refund_id = f"refund:{operation_id}"
            existing = await self.session.scalar(
                select(CreditLog).where(CreditLog.operation_id == refund_id)
            )
            if existing is not None:
                return existing.balance_after
            consume = await self.session.scalar(
                select(CreditLog).where(
                    CreditLog.operation_id == operation_id,
                    CreditLog.user_id == user_id,
                    CreditLog.type == "name_consume",
                )
            )
            if consume is None:
                raise ValueError("找不到可返还的扣次流水")
            credit.balance += abs(consume.change_count)
            credit.total_used = max(0, credit.total_used - abs(consume.change_count))
            self.session.add(CreditLog(
                user_id=user_id,
                change_count=abs(consume.change_count),
                balance_after=credit.balance,
                type="refund",
                remark=remark,
                operation_id=refund_id,
            ))
            await self.session.flush()
            return credit.balance

    async def adjust_credit_in_transaction(
        self,
        *,
        user_id: int,
        change_count: int,
        remark: str,
        operation_id: str,
    ) -> UserCredit:
        if change_count == 0:
            raise ValueError("调整次数不能为 0")
        credit = await self.session.scalar(
            select(UserCredit)
            .where(UserCredit.user_id == user_id)
            .with_for_update()
        )
        if credit is None:
            raise ValueError("用户次数账户不存在")
        existing = await self.session.scalar(
            select(CreditLog).where(CreditLog.operation_id == operation_id)
        )
        if existing is not None:
            if existing.user_id != user_id or existing.type != "admin_adjust":
                raise ValueError("幂等键已被其他业务使用")
            return credit
        if credit.balance + change_count < 0:
            raise ValueError("调整后余额不能小于 0")
        credit.balance += change_count
        self.session.add(CreditLog(
            user_id=user_id,
            change_count=change_count,
            balance_after=credit.balance,
            type="admin_adjust",
            remark=remark.strip(),
            operation_id=operation_id,
        ))
        await self.session.flush()
        return credit

    async def list_admin_accounts(
        self, *, limit: int = 100, offset: int = 0
    ) -> list[tuple[UserCredit, User]]:
        async with self.session.begin():
            return list((await self.session.execute(
                select(UserCredit, User)
                .join(User, User.id == UserCredit.user_id)
                .order_by(UserCredit.id.desc())
                .offset(offset)
                .limit(limit)
            )).all())
