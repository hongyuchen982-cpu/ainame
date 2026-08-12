from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from schemas.name_schemas import CategoryLiteral, NameIn


ProjectStatus = Literal["draft", "generated", "selected", "archived"]


class ProjectCreateIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    conditions: NameIn


class ProjectUpdateIn(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=120)
    conditions: NameIn | None = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if self.title is None and self.conditions is None:
            raise ValueError("没有需要修改的项目资料")
        return self


class ProjectCandidateOut(BaseModel):
    id: int
    name: str
    reference: str
    moral: str
    domain: str
    domain_status: str


class ProjectRoundOut(BaseModel):
    id: int
    round_no: int
    feedback: str
    created_at: datetime
    candidates: list[ProjectCandidateOut]


class ProjectFinalNameOut(BaseModel):
    id: int
    name: str
    reference: str
    moral: str
    logo_url: str
    logo_status: str
    can_generate_logo: bool


class ProjectListOut(BaseModel):
    id: int
    title: str
    category: CategoryLiteral
    status: ProjectStatus
    conditions: dict[str, Any]
    thread_id: str | None
    current_round: int
    final_name: str | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


class ProjectDetailOut(ProjectListOut):
    rounds: list[ProjectRoundOut]
    final_selection: ProjectFinalNameOut | None
