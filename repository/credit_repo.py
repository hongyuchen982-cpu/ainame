from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.user_credit import UserCredit, CreditLog

class CreditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_register_credit(self, user_id: int, gift_count: int = 3) -> UserCredit:
        """
        注册成功后，给用户创建次数账户，并赠送起名次数。
        """
        async with self.session.begin():
            credit = UserCredit(
                user_id=user_id,
                balance=gift_count,
                total_used=0,
                total_recharge=0,
            )
            self.session.add(credit)
            
            log = CreditLog(
                user_id=user_id,
                change_count=gift_count,
                balance_after=gift_count,
                type="register_gift",
                remark=f"注册赠送{gift_count}次起名机会",
            )
            self.session.add(log)
            
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
            credit = await self.session.scalar(
                select(UserCredit)
                .where(UserCredit.user_id == user_id)
                .with_for_update()
            )
            
            if not credit:
                raise ValueError("用户次数账户不存在")
            if credit.balance <= 0:
                raise ValueError("起名次数不足")
                
            credit.balance -= 1
            credit.total_used += 1
            
            log = CreditLog(
                user_id=user_id,
                change_count=-1,
                balance_after=credit.balance,
                type="name_consume",
                remark="AI起名消耗1次",
            )
            self.session.add(log)
            
            return credit.balance