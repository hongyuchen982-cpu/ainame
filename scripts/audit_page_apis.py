"""Audit every read API used while loading user and operations pages.

The target user's password, roles, and business data are never modified. A short-lived
device session is inserted for authentication and removed in the final cleanup. A fully
isolated administrator account is created for operations-page reads and then deleted.
"""

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import httpx
from sqlalchemy import delete, select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.authtools import AuthHandler
from models import AsyncSessionFactory, engine
from models.auth_models import Role, UserDevice, user_role
from models.user import User


@dataclass(frozen=True)
class Check:
    page: str
    path: str
    accepted: tuple[int, ...] = (200,)


USER_CHECKS = [
    Check("用户中心", "/users/me"),
    Check("用户中心", "/users/me/dashboard"),
    Check("用户中心", "/users/me/devices"),
    Check("用户中心", "/users/me/login-records"),
    Check("我的次数", "/credit/balance"),
    Check("我的次数", "/credit/account"),
    Check("我的次数", "/credit/logs"),
    Check("我的项目", "/projects"),
    Check("最终选名", "/name/selections"),
    Check("名称校验", "/validations"),
    Check("品牌资产", "/brand-assets"),
    Check("命名报告", "/reports"),
    Check("知识库", "/knowledge/files"),
    Check("异步任务", "/tasks"),
    Check("我的订单", "/pay/orders"),
    Check("套餐", "/package/list"),
    Check("专家服务", "/experts/packages"),
    Check("专家服务", "/experts/me"),
    Check("专家服务", "/experts/orders"),
    Check("社区投票", "/community/polls"),
    Check("开放平台", "/developers/account"),
    Check("开放平台", "/developers/plans"),
    Check("开放平台", "/developers/subscriptions"),
    Check("开放平台", "/developers/usage"),
    Check("开放平台", "/developers/usage/summary"),
    Check("邀请有礼", "/growth/promotion"),
    Check("邀请有礼", "/growth/referrals"),
    Check("邀请有礼", "/growth/rewards"),
    Check("邀请有礼", "/growth/commissions"),
]

ADMIN_CHECKS = [
    Check("运营看板", "/admin/dashboard"),
    Check("用户管理", "/admin/users"),
    Check("角色审计", "/admin/roles"),
    Check("角色审计", "/admin/permissions"),
    Check("角色审计", "/admin/audit-logs"),
    Check("次数管理", "/admin/credits"),
    Check("套餐管理", "/admin/packages"),
    Check("订单管理", "/admin/orders"),
    Check("项目管理", "/admin/projects"),
    Check("报告管理", "/admin/reports"),
    Check("知识库管理", "/admin/knowledge/files"),
    Check("任务管理", "/admin/tasks"),
    Check("名称校验管理", "/admin/validations"),
    Check("品牌资产管理", "/admin/brand-assets"),
    Check("专家服务管理", "/admin/experts/applications"),
    Check("专家服务管理", "/admin/experts/orders"),
    Check("专家服务管理", "/admin/experts/settlements"),
    Check("社区内容管理", "/admin/community/reports"),
    Check("开放平台管理", "/admin/developers"),
    Check("开放平台管理", "/developers/plans"),
    Check("增长活动管理", "/admin/growth/campaigns"),
    Check("增长活动管理", "/admin/growth/commissions"),
]


async def create_access(user_id: int, token_version: int, label: str) -> tuple[str, str]:
    device_id = str(uuid4())
    refresh_jti = str(uuid4())
    async with AsyncSessionFactory() as session:
        async with session.begin():
            session.add(UserDevice(
                id=device_id,
                user_id=user_id,
                device_name=label,
                user_agent="AI Name page API audit",
                ip_address="127.0.0.1",
                refresh_jti=refresh_jti,
            ))
    token = AuthHandler().encode_update_token(
        user_id=user_id,
        token_version=token_version,
        device_id=device_id,
    )["access_token"]
    return token, device_id


async def create_admin() -> User:
    email = f"__page_audit_admin_{uuid4().hex}@example.com"
    async with AsyncSessionFactory() as session:
        async with session.begin():
            admin = User(email=email, username="页面巡检管理员", password=uuid4().hex)
            session.add(admin)
            await session.flush()
            role_ids = list(await session.scalars(
                select(Role.id).where(Role.code.in_(["member", "admin"]))
            ))
            await session.execute(
                user_role.insert(),
                [{"user_id": admin.id, "role_id": role_id} for role_id in role_ids],
            )
            await session.flush()
            return admin


async def cleanup(device_ids: list[str], admin_id: int | None) -> None:
    async with AsyncSessionFactory() as session:
        async with session.begin():
            if device_ids:
                await session.execute(delete(UserDevice).where(UserDevice.id.in_(device_ids)))
            if admin_id is not None:
                await session.execute(delete(user_role).where(user_role.c.user_id == admin_id))
                await session.execute(delete(User).where(User.id == admin_id))


async def run_checks(client: httpx.AsyncClient, token: str, checks: list[Check]) -> list[tuple[Check, int, str]]:
    failures = []
    headers = {"Authorization": f"Bearer {token}"}
    for check in checks:
        try:
            response = await client.get(check.path, headers=headers)
            if response.status_code not in check.accepted:
                failures.append((check, response.status_code, response.text[:500]))
                print(f"FAIL | {check.page:<12} | {response.status_code} | {check.path} | {response.text[:160]}")
            else:
                print(f" OK  | {check.page:<12} | {response.status_code} | {check.path}")
        except Exception as exc:
            failures.append((check, 0, str(exc)))
            print(f"FAIL | {check.page:<12} | NETWORK | {check.path} | {exc}")
    return failures


async def main(email: str, base_url: str) -> int:
    device_ids: list[str] = []
    admin_id = None
    try:
        async with AsyncSessionFactory() as session:
            user = await session.scalar(select(User).where(User.email == email))
        if user is None:
            raise RuntimeError(f"Target user does not exist: {email}")

        user_token, user_device = await create_access(user.id, user.token_version, "页面巡检用户设备")
        device_ids.append(user_device)
        admin = await create_admin()
        admin_id = admin.id
        admin_token, admin_device = await create_access(admin.id, admin.token_version, "页面巡检管理员设备")
        device_ids.append(admin_device)

        async with httpx.AsyncClient(base_url=base_url, timeout=30) as client:
            print(f"\nUSER PAGE APIs ({email})")
            user_failures = await run_checks(client, user_token, USER_CHECKS)
            print("\nADMIN PAGE APIs")
            admin_failures = await run_checks(client, admin_token, ADMIN_CHECKS)
        failures = user_failures + admin_failures
        print(f"\nSUMMARY: {len(USER_CHECKS) + len(ADMIN_CHECKS) - len(failures)} passed, {len(failures)} failed")
        return 1 if failures else 0
    finally:
        await cleanup(device_ids, admin_id)
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit all read APIs used by frontend pages")
    parser.add_argument("--email", required=True, help="Existing member account to audit")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.email, args.base_url.rstrip("/"))))
