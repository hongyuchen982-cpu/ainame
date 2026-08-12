from datetime import datetime
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.auth_models import (
    AdminAuditLog,
    LoginRecord,
    Permission,
    Role,
    UserDevice,
    role_permission,
    user_role,
)
from models.user import User


class SecurityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def assign_default_role(self, user_id: int) -> None:
        async with self.session.begin():
            await self.assign_default_role_in_transaction(user_id)

    async def assign_default_role_in_transaction(self, user_id: int) -> None:
        """在调用方已经开启的事务中分配默认角色。"""
        role_id = await self.session.scalar(select(Role.id).where(Role.code == "member"))
        if role_id is None:
            raise RuntimeError("系统默认角色 member 不存在")
        await self.session.execute(
            user_role.insert().values(user_id=user_id, role_id=role_id)
        )

    async def get_role_codes(self, user_id: int) -> list[str]:
        async with self.session.begin():
            result = await self.session.scalars(
                select(Role.code)
                .join(user_role, user_role.c.role_id == Role.id)
                .where(user_role.c.user_id == user_id)
                .order_by(Role.id)
            )
            return list(result)

    async def get_permission_codes(self, user_id: int) -> set[str]:
        async with self.session.begin():
            result = await self.session.scalars(
                select(Permission.code)
                .join(role_permission, role_permission.c.permission_id == Permission.id)
                .join(Role, Role.id == role_permission.c.role_id)
                .join(user_role, user_role.c.role_id == Role.id)
                .where(user_role.c.user_id == user_id)
            )
            return set(result)

    async def create_device(
        self,
        *,
        user_id: int,
        user_agent: str,
        ip_address: str,
        refresh_jti: str,
    ) -> UserDevice:
        async with self.session.begin():
            device = UserDevice(
                id=str(uuid4()),
                user_id=user_id,
                device_name=self._device_name(user_agent),
                user_agent=user_agent[:500],
                ip_address=ip_address[:64],
                refresh_jti=refresh_jti,
            )
            self.session.add(device)
            await self.session.flush()
            return device

    async def touch_device(self, device_id: str, user_id: int) -> UserDevice | None:
        async with self.session.begin():
            device = await self.session.scalar(
                select(UserDevice).where(
                    UserDevice.id == device_id,
                    UserDevice.user_id == user_id,
                    UserDevice.revoked_at.is_(None),
                )
            )
            if device:
                device.last_seen_at = datetime.now()
            return device

    async def rotate_refresh_token(
        self,
        device_id: str,
        user_id: int,
        current_refresh_jti: str,
        refresh_jti: str,
    ) -> UserDevice | None:
        """轮换设备 Refresh Token；旧 Token 在提交后立即失效。"""
        async with self.session.begin():
            device = await self.session.scalar(
                select(UserDevice)
                .where(
                    UserDevice.id == device_id,
                    UserDevice.user_id == user_id,
                    UserDevice.revoked_at.is_(None),
                )
                .with_for_update()
            )
            if device is None:
                return None
            if device.refresh_jti != current_refresh_jti:
                return None
            device.refresh_jti = refresh_jti
            device.last_seen_at = datetime.now()
            await self.session.flush()
            return device

    async def list_devices(self, user_id: int) -> list[UserDevice]:
        async with self.session.begin():
            result = await self.session.scalars(
                select(UserDevice)
                .where(UserDevice.user_id == user_id)
                .order_by(UserDevice.last_seen_at.desc())
            )
            return list(result)

    async def revoke_device(self, device_id: str, user_id: int) -> bool:
        async with self.session.begin():
            device = await self.session.scalar(
                select(UserDevice).where(
                    UserDevice.id == device_id,
                    UserDevice.user_id == user_id,
                )
            )
            if device is None:
                return False
            device.revoked_at = datetime.now()
            return True

    async def revoke_all_devices(self, user_id: int) -> None:
        async with self.session.begin():
            await self.revoke_all_devices_in_transaction(user_id)

    async def revoke_all_devices_in_transaction(self, user_id: int) -> None:
        devices = await self.session.scalars(
            select(UserDevice).where(
                UserDevice.user_id == user_id,
                UserDevice.revoked_at.is_(None),
            )
        )
        now = datetime.now()
        for device in devices:
            device.revoked_at = now

    async def record_login(
        self,
        *,
        email: str,
        user_id: int | None,
        device_id: str = "",
        ip_address: str = "",
        user_agent: str = "",
        success: bool,
        failure_reason: str = "",
    ) -> None:
        async with self.session.begin():
            self.session.add(LoginRecord(
                user_id=user_id,
                email=email,
                device_id=device_id,
                ip_address=ip_address[:64],
                user_agent=user_agent[:500],
                success=success,
                failure_reason=failure_reason[:200],
            ))

    async def list_login_records(self, user_id: int, limit: int = 50) -> list[LoginRecord]:
        async with self.session.begin():
            result = await self.session.scalars(
                select(LoginRecord)
                .where(LoginRecord.user_id == user_id)
                .order_by(LoginRecord.created_at.desc())
                .limit(limit)
            )
            return list(result)

    async def list_roles(self) -> list[Role]:
        async with self.session.begin():
            result = await self.session.scalars(select(Role).order_by(Role.id))
            return list(result)

    async def list_permissions(self) -> list[Permission]:
        async with self.session.begin():
            result = await self.session.scalars(select(Permission).order_by(Permission.id))
            return list(result)

    async def get_role_permission_codes(self, role_id: int) -> list[str]:
        async with self.session.begin():
            result = await self.session.scalars(
                select(Permission.code)
                .join(role_permission, role_permission.c.permission_id == Permission.id)
                .where(role_permission.c.role_id == role_id)
                .order_by(Permission.id)
            )
            return list(result)

    async def create_role(
        self,
        *,
        code: str,
        name: str,
        description: str,
        permission_codes: list[str],
    ) -> Role:
        async with self.session.begin():
            return await self.create_role_in_transaction(
                code=code,
                name=name,
                description=description,
                permission_codes=permission_codes,
            )

    async def create_role_in_transaction(
        self,
        *,
        code: str,
        name: str,
        description: str,
        permission_codes: list[str],
    ) -> Role:
        if await self.session.scalar(select(Role.id).where(Role.code == code)):
            raise ValueError("角色代码已经存在")
        permissions = list(await self.session.scalars(
            select(Permission).where(Permission.code.in_(permission_codes))
        )) if permission_codes else []
        if len(permissions) != len(set(permission_codes)):
            raise ValueError("包含不存在的权限")
        role = Role(
            code=code,
            name=name,
            description=description,
            is_system=False,
        )
        self.session.add(role)
        await self.session.flush()
        if permissions:
            await self.session.execute(
                role_permission.insert(),
                [{"role_id": role.id, "permission_id": item.id} for item in permissions],
            )
        return role

    async def replace_role_permissions(
        self,
        role_code: str,
        permission_codes: list[str],
    ) -> Role | None:
        async with self.session.begin():
            return await self.replace_role_permissions_in_transaction(
                role_code, permission_codes
            )

    async def replace_role_permissions_in_transaction(
        self,
        role_code: str,
        permission_codes: list[str],
    ) -> Role | None:
        role = await self.session.scalar(select(Role).where(Role.code == role_code))
        if role is None:
            return None
        if role.is_system:
            raise ValueError("系统角色权限不能通过接口修改")
        permissions = list(await self.session.scalars(
            select(Permission).where(Permission.code.in_(permission_codes))
        )) if permission_codes else []
        if len(permissions) != len(set(permission_codes)):
            raise ValueError("包含不存在的权限")
        await self.session.execute(
            delete(role_permission).where(role_permission.c.role_id == role.id)
        )
        if permissions:
            await self.session.execute(
                role_permission.insert(),
                [{"role_id": role.id, "permission_id": item.id} for item in permissions],
            )
        return role

    async def replace_user_roles(self, user_id: int, role_codes: list[str]) -> list[str]:
        async with self.session.begin():
            return await self.replace_user_roles_in_transaction(user_id, role_codes)

    async def replace_user_roles_in_transaction(
        self, user_id: int, role_codes: list[str]
    ) -> list[str]:
        user = await self.session.get(User, user_id)
        if user is None:
            raise ValueError("用户不存在")
        roles = list(await self.session.scalars(select(Role).where(Role.code.in_(role_codes))))
        if len(roles) != len(set(role_codes)):
            raise ValueError("包含不存在的角色")
        await self.session.execute(delete(user_role).where(user_role.c.user_id == user_id))
        if roles:
            await self.session.execute(
                user_role.insert(),
                [{"user_id": user_id, "role_id": role.id} for role in roles],
            )
        user.token_version += 1
        return [role.code for role in roles]

    async def audit(
        self,
        *,
        admin_user_id: int,
        action: str,
        target_type: str,
        target_id: str,
        detail: str,
        ip_address: str,
    ) -> None:
        async with self.session.begin():
            await self.audit_in_transaction(
                admin_user_id=admin_user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                detail=detail,
                ip_address=ip_address,
            )

    async def audit_in_transaction(
        self,
        *,
        admin_user_id: int,
        action: str,
        target_type: str,
        target_id: str,
        detail: str,
        ip_address: str,
    ) -> None:
        self.session.add(AdminAuditLog(
            admin_user_id=admin_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip_address=ip_address[:64],
        ))
        await self.session.flush()

    async def list_audit_logs(self, limit: int = 100) -> list[AdminAuditLog]:
        async with self.session.begin():
            result = await self.session.scalars(
                select(AdminAuditLog)
                .order_by(AdminAuditLog.created_at.desc())
                .limit(limit)
            )
            return list(result)

    @staticmethod
    def _device_name(user_agent: str) -> str:
        agent = user_agent.lower()
        browser = "Chrome" if "chrome" in agent else "Safari" if "safari" in agent else "Firefox" if "firefox" in agent else "浏览器"
        system = "Windows" if "windows" in agent else "iPhone" if "iphone" in agent else "Android" if "android" in agent else "Mac" if "macintosh" in agent else "未知系统"
        return f"{system} · {browser}"
