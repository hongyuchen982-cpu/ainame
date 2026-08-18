from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from schemas.name_schemas import NameIn, NameSchema


class DeveloperCreateIn(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=160)
    contact_name: str = Field(..., min_length=2, max_length=100)
    use_case: str = Field(..., min_length=10, max_length=3000)


class DeveloperOut(BaseModel):
    id: int; company_name: str; contact_name: str; use_case: str; status: str; created_at: datetime


class ApiKeyCreateIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


class ApiKeyOut(BaseModel):
    id: int; name: str; key_prefix: str; status: str; created_at: datetime; last_used_at: datetime | None; revoked_at: datetime | None


class ApiKeyCreatedOut(ApiKeyOut):
    api_key: str


class ApiPlanIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field("", max_length=500)
    price: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2)
    quota_calls: int = Field(..., ge=1, le=10_000_000)
    validity_days: int = Field(..., ge=1, le=3650)


class ApiPlanOut(ApiPlanIn):
    id: int; is_active: bool; created_at: datetime


class ApiSubscriptionOut(BaseModel):
    id: int; plan_id: int; plan_name: str; quota_total: int; quota_used: int; quota_remaining: int; status: str; starts_at: datetime; expires_at: datetime


class ApiNamingIn(NameIn):
    project_id: None = None
    request_id: str = Field(..., min_length=8, max_length=100)


class ApiBatchNamingIn(BaseModel):
    request_id: str = Field(..., min_length=8, max_length=100)
    items: list[NameIn] = Field(..., min_length=1, max_length=10)


class ApiNamingResult(BaseModel):
    names: list[NameSchema]


class ApiBatchResult(BaseModel):
    results: list[ApiNamingResult]


class ApiUsageOut(BaseModel):
    id: int; request_id: str; endpoint: str; units: int; status: str; error_message: str; latency_ms: int; created_at: datetime


class ApiUsageSummaryOut(BaseModel):
    calls_total: int; units_total: int; success_total: int; failed_total: int


class ApiGrantIn(BaseModel):
    plan_id: int = Field(..., ge=1)


class DeveloperStatusIn(BaseModel):
    status: Literal["active", "suspended"]
