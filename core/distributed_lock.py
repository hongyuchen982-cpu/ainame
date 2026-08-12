import asyncio
from contextlib import asynccontextmanager, suppress
from typing import AsyncIterator

from redis.asyncio import Redis
from redis.exceptions import LockError


class OperationBusyError(RuntimeError):
    """同一业务资源上已经有一个耗时操作正在执行。"""


@asynccontextmanager
async def distributed_operation_lock(
    redis: Redis,
    key: str,
    *,
    timeout: int = 300,
) -> AsyncIterator[None]:
    """持有可自动续期的 Redis 锁，避免同一命名会话并发调用 AI。"""

    lock = redis.lock(key, timeout=timeout, blocking=False)
    if not await lock.acquire(blocking=False):
        raise OperationBusyError("该命名任务正在处理中，请勿重复提交")

    stopped = asyncio.Event()

    async def keep_alive() -> None:
        while True:
            try:
                await asyncio.wait_for(stopped.wait(), timeout=max(1, timeout // 3))
                return
            except TimeoutError:
                try:
                    await lock.extend(timeout, replace_ttl=True)
                except LockError:
                    return

    renew_task = asyncio.create_task(keep_alive())
    try:
        yield
    finally:
        stopped.set()
        renew_task.cancel()
        with suppress(asyncio.CancelledError):
            await renew_task
        with suppress(LockError):
            await lock.release()
