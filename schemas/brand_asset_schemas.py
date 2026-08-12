from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BrandAssetCreateIn(BaseModel):
    selected_name_id: int = Field(..., ge=1)
    client_request_id: str = Field(..., min_length=8, max_length=100)
    validation_id: int | None = Field(None, ge=1)
    brief: str = Field("", max_length=1200)

    @field_validator("brief")
    @classmethod
    def clean_brief(cls, value: str) -> str:
        return value.strip()


class BrandPositioning(BaseModel):
    target_audience: str = Field(..., min_length=2, max_length=300)
    market_category: str = Field(..., min_length=2, max_length=200)
    core_value: str = Field(..., min_length=2, max_length=300)
    brand_personality: list[str] = Field(..., min_length=2, max_length=6)
    differentiation: str = Field(..., min_length=2, max_length=300)
    positioning_statement: str = Field(..., min_length=2, max_length=500)


class SloganIdea(BaseModel):
    text: str = Field(..., min_length=2, max_length=60)
    tone: str = Field(..., min_length=1, max_length=40)
    rationale: str = Field(..., min_length=2, max_length=240)


class LogoConcept(BaseModel):
    title: str = Field(..., min_length=2, max_length=60)
    symbol: str = Field(..., min_length=2, max_length=240)
    composition: str = Field(..., min_length=2, max_length=240)
    colors: list[str] = Field(..., min_length=2, max_length=5)
    typography: str = Field(..., min_length=2, max_length=160)
    rationale: str = Field(..., min_length=2, max_length=240)


class ColorIdea(BaseModel):
    name: str = Field(..., min_length=1, max_length=30)
    hex: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    usage: str = Field(..., min_length=2, max_length=120)


class VisualGuidelines(BaseModel):
    colors: list[ColorIdea] = Field(..., min_length=3, max_length=6)
    typography: str = Field(..., min_length=2, max_length=240)
    imagery: str = Field(..., min_length=2, max_length=240)
    layout: str = Field(..., min_length=2, max_length=240)
    avoid: list[str] = Field(..., min_length=2, max_length=6)


class RiskAdvice(BaseModel):
    category: str = Field(..., min_length=2, max_length=40)
    level: Literal["low", "medium", "high", "unknown"]
    note: str = Field(..., min_length=2, max_length=300)
    action: str = Field(..., min_length=2, max_length=300)


class BrandAssetGenerated(BaseModel):
    positioning: BrandPositioning
    slogans: list[SloganIdea] = Field(..., min_length=3, max_length=6)
    logo_concepts: list[LogoConcept] = Field(..., min_length=2, max_length=4)
    visual_guidelines: VisualGuidelines
    risk_notes: list[RiskAdvice] = Field(..., min_length=2, max_length=8)


class BrandAssetOut(BaseModel):
    id: int
    selected_name_id: int
    project_id: int | None
    validation_id: int | None
    client_request_id: str
    name: str
    brief: str
    positioning: dict[str, Any]
    slogans: list[dict[str, Any]]
    logo_concepts: list[dict[str, Any]]
    visual_guidelines: dict[str, Any]
    domain_matrix: list[dict[str, Any]]
    risk_notes: list[dict[str, Any]]
    validation_snapshot: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminBrandAssetOut(BrandAssetOut):
    user_id: int
    user_email: str
    username: str
