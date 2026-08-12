from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NamingReportCreateIn(BaseModel):
    project_id: int = Field(..., ge=1)
    client_request_id: str = Field(..., min_length=8, max_length=100)
    validation_id: int | None = Field(None, ge=1)
    brand_asset_id: int | None = Field(None, ge=1)


class NamingReportOut(BaseModel):
    id: int
    project_id: int
    selected_name_id: int
    validation_id: int | None
    brand_asset_id: int | None
    client_request_id: str
    title: str
    name: str
    file_size: int
    page_count: int
    sha256: str
    download_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminNamingReportOut(NamingReportOut):
    user_id: int
    user_email: str
    username: str
