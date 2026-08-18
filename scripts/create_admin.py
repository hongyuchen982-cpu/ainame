"""创建或提升首个管理员账号。

用法：python scripts/create_admin.py admin@example.com
"""

import argparse
import asyncio
import getpass
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import select

from models import AsyncSessionFactory
from models.auth_models import Role, user_role
from models.user import User


async def create_admin(email: str, username: str | None) -> None:
    async with AsyncSessionFactory() as session:
        async with session.begin():
            user = await session.scalar(select(User).where(User.email == email))
            if user is None:
                password = getpass.getpass("管理员初始密码：")
                confirm = getpass.getpass("再次输入密码：")
                if password != confirm or len(password) < 6:
                    raise ValueError("两次密码不一致，或密码少于 6 位")
                user = User(
                    email=email,
                    username=username or "系统管理员",
                    password=password,
                )
                session.add(user)
                await session.flush()

            roles = list(await session.scalars(
                select(Role).where(Role.code.in_(["member", "admin"]))
            ))
            if not any(role.code == "admin" for role in roles):
                raise RuntimeError("admin 角色不存在，请先执行 alembic upgrade head")

            existing = set(await session.scalars(
                select(user_role.c.role_id).where(user_role.c.user_id == user.id)
            ))
            new_rows = [
                {"user_id": user.id, "role_id": role.id}
                for role in roles
                if role.id not in existing
            ]
            if new_rows:
                await session.execute(user_role.insert(), new_rows)
            user.status = "active"
            user.token_version += 1

        print(f"管理员账号已就绪：{email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="创建或提升管理员账号")
    parser.add_argument("email")
    parser.add_argument("--username")
    args = parser.parse_args()
    asyncio.run(create_admin(args.email, args.username))


if __name__ == "__main__":
    main()
