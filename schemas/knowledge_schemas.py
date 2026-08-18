from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KnowledgeFileOut(BaseModel):
    id: int
    original_name: str
    extension: str
    mime_type: str
    size_bytes: int
    status: str
    processing_version: int
    attempt_count: int
    chunk_count: int
    error_message: str
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AdminKnowledgeFileOut(KnowledgeFileOut):
    user_id: int
    user_email: str
    username: str


class KnowledgeUploadOut(BaseModel):
    result: str
    message: str
    file: KnowledgeFileOut
    task_id: str
