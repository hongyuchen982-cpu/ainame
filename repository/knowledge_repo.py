from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.knowledge_file import KnowledgeFile
from models.user import User


class KnowledgeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_in_transaction(self, **values) -> KnowledgeFile:
        item = KnowledgeFile(**values)
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_for_user(self, user_id: int) -> list[KnowledgeFile]:
        async with self.session.begin():
            return list(await self.session.scalars(
                select(KnowledgeFile)
                .where(KnowledgeFile.user_id == user_id, KnowledgeFile.status != "deleted")
                .order_by(KnowledgeFile.id.desc())
            ))

    async def get_for_user(self, file_id: int, user_id: int) -> KnowledgeFile | None:
        async with self.session.begin():
            return await self.session.scalar(select(KnowledgeFile).where(
                KnowledgeFile.id == file_id,
                KnowledgeFile.user_id == user_id,
                KnowledgeFile.status != "deleted",
            ))

    async def list_all(self, status: str | None = None) -> list[tuple[KnowledgeFile, User]]:
        async with self.session.begin():
            statement = (
                select(KnowledgeFile, User)
                .join(User, User.id == KnowledgeFile.user_id)
                .where(KnowledgeFile.status != "deleted")
                .order_by(KnowledgeFile.id.desc())
            )
            if status:
                statement = statement.where(KnowledgeFile.status == status)
            return list((await self.session.execute(statement)).all())

    async def mark_enqueue_failed(self, file_id: int, error: str) -> None:
        async with self.session.begin():
            item = await self.session.get(KnowledgeFile, file_id, with_for_update=True)
            if item and item.status == "queued":
                item.status = "failed"
                item.error_message = error[:2000]

    async def retry(self, file_id: int, user_id: int | None = None) -> KnowledgeFile | None:
        async with self.session.begin():
            statement = select(KnowledgeFile).where(KnowledgeFile.id == file_id).with_for_update()
            if user_id is not None:
                statement = statement.where(KnowledgeFile.user_id == user_id)
            item = await self.session.scalar(statement)
            if item is None or item.status == "deleted":
                return None
            if item.status not in {"failed", "completed"}:
                raise ValueError("只有处理失败或已完成的文件可以重新处理")
            item.status = "queued"
            item.processing_version += 1
            item.error_message = ""
            item.processed_at = None
            await self.session.flush()
            return item

    async def mark_deleted(self, file_id: int, user_id: int | None = None) -> KnowledgeFile | None:
        async with self.session.begin():
            statement = select(KnowledgeFile).where(KnowledgeFile.id == file_id).with_for_update()
            if user_id is not None:
                statement = statement.where(KnowledgeFile.user_id == user_id)
            item = await self.session.scalar(statement)
            if item is None or item.status == "deleted":
                return None
            item.status = "deleting"
            item.processing_version += 1
            item.error_message = ""
            await self.session.flush()
            return item

    async def finish_delete(self, file_id: int, version: int) -> bool:
        async with self.session.begin():
            item = await self.session.get(KnowledgeFile, file_id, with_for_update=True)
            if item is None or item.status != "deleting" or item.processing_version != version:
                return False
            item.status = "deleted"
            item.deleted_at = datetime.now()
            return True

    async def fail_delete(self, file_id: int, version: int, error: str) -> bool:
        async with self.session.begin():
            item = await self.session.get(KnowledgeFile, file_id, with_for_update=True)
            if item is None or item.status != "deleting" or item.processing_version != version:
                return False
            item.status = "failed"
            item.error_message = f"删除失败：{error}"[:2000]
            return True

    async def claim_processing(
        self, file_id: int, version: int, *, allow_resume: bool = False
    ) -> KnowledgeFile | None:
        async with self.session.begin():
            item = await self.session.get(KnowledgeFile, file_id, with_for_update=True)
            valid_status = item is not None and (
                item.status == "queued" or (allow_resume and item.status == "processing")
            )
            if not valid_status or item.processing_version != version:
                return None
            item.status = "processing"
            item.attempt_count += 1
            item.error_message = ""
            await self.session.flush()
            return item

    async def finish_processing(self, file_id: int, version: int, chunk_count: int) -> bool:
        async with self.session.begin():
            item = await self.session.get(KnowledgeFile, file_id, with_for_update=True)
            if item is None or item.status != "processing" or item.processing_version != version:
                return False
            item.status = "completed"
            item.chunk_count = chunk_count
            item.processed_at = datetime.now()
            item.error_message = ""
            return True

    async def fail_processing(self, file_id: int, version: int, error: str) -> bool:
        async with self.session.begin():
            item = await self.session.get(KnowledgeFile, file_id, with_for_update=True)
            if item is None or item.status != "processing" or item.processing_version != version:
                return False
            item.status = "failed"
            item.error_message = error[:2000]
            return True

    async def schedule_retry(self, file_id: int, version: int, error: str) -> bool:
        async with self.session.begin():
            item = await self.session.get(KnowledgeFile, file_id, with_for_update=True)
            if item is None or item.status != "processing" or item.processing_version != version:
                return False
            item.status = "queued"
            item.error_message = f"自动重试中：{error}"[:2000]
            return True

    async def prepare_task_retry(self, file_id: int, version: int) -> bool:
        async with self.session.begin():
            item = await self.session.get(KnowledgeFile, file_id, with_for_update=True)
            if item is None or item.processing_version != version or item.status == "deleted":
                return False
            if item.status not in {"failed", "queued"}:
                return False
            item.status = "queued"
            item.error_message = ""
            item.processed_at = None
            return True

    async def cancel_queued(self, file_id: int, version: int, reason: str) -> bool:
        async with self.session.begin():
            item = await self.session.get(KnowledgeFile, file_id, with_for_update=True)
            if item is None or item.processing_version != version or item.status != "queued":
                return False
            item.status = "failed"
            item.error_message = reason[:2000]
            return True
