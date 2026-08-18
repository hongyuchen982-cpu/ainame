from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AsyncTaskOut(BaseModel):
    id: str
    task_type: str
    target_type: str
    target_id: str
    status: str
    progress: int
    attempt_count: int
    max_attempts: int
    result: str
    error_message: str
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    next_retry_at: datetime | None
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AdminAsyncTaskOut(AsyncTaskOut):
    user_id: int
    user_email: str
    username: str


class TaskProgressIn(BaseModel):
    progress: int = Field(..., ge=0, le=100)
