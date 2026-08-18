from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NameValidationCreateIn(BaseModel):
    selected_name_id: int = Field(..., ge=1)
    client_request_id: str = Field(..., min_length=8, max_length=100)
    domain_stem: str = Field(..., min_length=1, max_length=63)
    suffixes: list[str] = Field(default_factory=lambda: ["com", "cn", "net", "io"], min_length=1, max_length=8)

    @field_validator("domain_stem")
    @classmethod
    def validate_stem(cls, value: str) -> str:
        value = value.strip().lower()
        if value.startswith("-") or value.endswith("-") or not all(ch.isascii() and (ch.isalnum() or ch == "-") for ch in value):
            raise ValueError("域名前缀只能包含英文字母、数字和中划线，且不能以中划线开头或结尾")
        return value

    @field_validator("suffixes")
    @classmethod
    def validate_suffixes(cls, values: list[str]) -> list[str]:
        normalized = []
        for value in values:
            suffix = value.strip().lower().lstrip(".")
            if not 2 <= len(suffix) <= 20 or not all(ch.isascii() and (ch.isalnum() or ch == "-") for ch in suffix):
                raise ValueError(f"无效域名后缀：{value}")
            if suffix not in normalized:
                normalized.append(suffix)
        return normalized


class NameValidationOut(BaseModel):
    id: int
    selected_name_id: int
    project_id: int | None
    client_request_id: str
    name: str
    domain_stem: str
    status: str
    domains: list[dict[str, Any]]
    trademark: dict[str, Any]
    company: dict[str, Any]
    social: dict[str, Any]
    risk_score: int
    risk_level: str
    coverage: int
    risk_summary: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminNameValidationOut(NameValidationOut):
    user_id: int
    user_email: str
    username: str
