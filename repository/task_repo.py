import json
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.async_task import AsyncTask
from models.user import User


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_in_transaction(
        self,
        *,
        user_id: int,
        task_type: str,
        target_type: str,
        target_id: str,
        payload: dict,
        max_attempts: int = 3,
    ) -> AsyncTask:
        task = AsyncTask(
            user_id=user_id,
            task_type=task_type,
            target_type=target_type,
            target_id=target_id,
            payload=json.dumps(payload, ensure_ascii=False),
            max_attempts=max_attempts,
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def create(self, **values) -> AsyncTask:
        async with self.session.begin():
            return await self.create_in_transaction(**values)

    async def list_for_user(self, user_id: int, status: str | None = None) -> list[AsyncTask]:
        async with self.session.begin():
            statement = select(AsyncTask).where(AsyncTask.user_id == user_id)
            if status:
                statement = statement.where(AsyncTask.status == status)
            return list(await self.session.scalars(statement.order_by(AsyncTask.created_at.desc()).limit(100)))

    async def get_for_user(self, task_id: str, user_id: int) -> AsyncTask | None:
        async with self.session.begin():
            return await self.session.scalar(select(AsyncTask).where(
                AsyncTask.id == task_id, AsyncTask.user_id == user_id
            ))

    async def get(self, task_id: str) -> AsyncTask | None:
        async with self.session.begin():
            return await self.session.get(AsyncTask, task_id)

    async def list_all(self, status: str | None = None, task_type: str | None = None) -> list[tuple[AsyncTask, User]]:
        async with self.session.begin():
            statement = select(AsyncTask, User).join(User, User.id == AsyncTask.user_id)
            if status:
                statement = statement.where(AsyncTask.status == status)
            if task_type:
                statement = statement.where(AsyncTask.task_type == task_type)
            return list((await self.session.execute(
                statement.order_by(AsyncTask.created_at.desc()).limit(200)
            )).all())

    async def claim(self, task_id: str) -> AsyncTask | None:
        async with self.session.begin():
            task = await self.session.get(AsyncTask, task_id, with_for_update=True)
            if task is None:
                return None
            stale_running = (
                task.status == "running"
                and task.updated_at <= datetime.now() - timedelta(minutes=2)
            )
            if task.status != "queued" and not stale_running:
                return None
            if task.attempt_count >= task.max_attempts:
                task.status = "failed"
                task.finished_at = datetime.now()
                task.error_message = task.error_message or "已达到最大重试次数"
                return None
            task.status = "running"
            task.progress = 10
            task.attempt_count += 1
            task.started_at = datetime.now()
            task.next_retry_at = None
            return task

    async def heartbeat(self, task_id: str) -> bool:
        async with self.session.begin():
            task = await self.session.get(AsyncTask, task_id, with_for_update=True)
            if task is None or task.status != "running":
                return False
            task.updated_at = datetime.now()
            return True

    async def set_progress(self, task_id: str, progress: int) -> bool:
        async with self.session.begin():
            task = await self.session.get(AsyncTask, task_id, with_for_update=True)
            if task is None or task.status != "running":
                return False
            task.progress = max(task.progress, min(progress, 99))
            return True

    async def complete(self, task_id: str, result: dict) -> bool:
        async with self.session.begin():
            task = await self.session.get(AsyncTask, task_id, with_for_update=True)
            if task is None or task.status != "running":
                return False
            task.status = "completed"
            task.progress = 100
            task.result = json.dumps(result, ensure_ascii=False)
            task.error_message = ""
            task.finished_at = datetime.now()
            return True

    async def cancel_stale(self, task_id: str, reason: str) -> bool:
        async with self.session.begin():
            task = await self.session.get(AsyncTask, task_id, with_for_update=True)
            if task is None or task.status not in {"queued", "running"}:
                return False
            task.status = "canceled"
            task.error_message = reason[:2000]
            task.finished_at = datetime.now()
            return True

    async def fail_or_retry(self, task_id: str, error: str) -> bool:
        """Record an execution error and return whether RabbitMQ should requeue it."""
        async with self.session.begin():
            task = await self.session.get(AsyncTask, task_id, with_for_update=True)
            if task is None or task.status != "running":
                return False
            task.error_message = error[:2000]
            task.progress = 0
            if task.attempt_count < task.max_attempts:
                task.status = "queued"
                task.next_retry_at = datetime.now() + timedelta(seconds=min(2 ** task.attempt_count, 30))
                return True
            task.status = "failed"
            task.finished_at = datetime.now()
            return False

    async def mark_enqueue_failed(self, task_id: str, error: str) -> None:
        async with self.session.begin():
            task = await self.session.get(AsyncTask, task_id, with_for_update=True)
            if task and task.status == "queued":
                task.status = "failed"
                task.error_message = error[:2000]
                task.finished_at = datetime.now()

    async def manual_retry(self, task_id: str, user_id: int | None = None) -> AsyncTask | None:
        async with self.session.begin():
            statement = select(AsyncTask).where(AsyncTask.id == task_id).with_for_update()
            if user_id is not None:
                statement = statement.where(AsyncTask.user_id == user_id)
            task = await self.session.scalar(statement)
            if task is None:
                return None
            if task.status not in {"failed", "canceled"}:
                raise ValueError("只有失败或已取消的任务可以重试")
            task.status = "queued"
            task.progress = 0
            task.attempt_count = 0
            task.error_message = ""
            task.result = "{}"
            task.started_at = None
            task.finished_at = None
            task.next_retry_at = None
            return task

    async def cancel(self, task_id: str) -> AsyncTask | None:
        async with self.session.begin():
            task = await self.session.get(AsyncTask, task_id, with_for_update=True)
            if task is None:
                return None
            if task.status != "queued":
                raise ValueError("只有排队中的任务可以取消")
            task.status = "canceled"
            task.finished_at = datetime.now()
            task.error_message = "管理员已取消任务"
            return task

    async def cancel_queued_for_target(self, target_type: str, target_id: str) -> int:
        async with self.session.begin():
            result = await self.session.execute(
                update(AsyncTask)
                .where(
                    AsyncTask.target_type == target_type,
                    AsyncTask.target_id == target_id,
                    AsyncTask.status == "queued",
                )
                .values(
                    status="canceled",
                    error_message="关联业务对象已删除",
                    finished_at=datetime.now(),
                )
            )
            return result.rowcount or 0
