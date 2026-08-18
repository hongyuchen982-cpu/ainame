from datetime import datetime

from pydantic import BaseModel, Field


class CommunityPollCreateIn(BaseModel):
    project_id: int = Field(..., ge=1)
    title: str = Field(..., min_length=4, max_length=160)
    description: str = Field("", max_length=3000)
    candidate_ids: list[int] = Field(..., min_length=2, max_length=12)


class CommunityCandidateOut(BaseModel):
    id: int
    name: str
    reference: str
    moral: str
    vote_count: int
    vote_percent: float


class CommunityCommentOut(BaseModel):
    id: int
    username: str
    content: str
    created_at: datetime


class CommunityPollOut(BaseModel):
    id: int
    title: str
    description: str
    category: str
    status: str
    is_featured: bool
    publisher: str
    can_manage: bool
    vote_count: int
    comment_count: int
    my_candidate_id: int | None
    candidates: list[CommunityCandidateOut]
    comments: list[CommunityCommentOut]
    created_at: datetime
    closed_at: datetime | None


class CommunityVoteIn(BaseModel):
    candidate_id: int = Field(..., ge=1)


class CommunityCommentIn(BaseModel):
    content: str = Field(..., min_length=2, max_length=1000)


class CommunityReportIn(BaseModel):
    target_type: str = Field(..., pattern="^(poll|comment)$")
    target_id: int = Field(..., ge=1)
    reason: str = Field(..., min_length=5, max_length=500)


class CommunityReportOut(BaseModel):
    id: int
    reporter: str
    target_type: str
    target_id: int
    reason: str
    status: str
    resolution: str
    created_at: datetime
    resolved_at: datetime | None


class CommunityFeatureIn(BaseModel):
    is_featured: bool


class CommunityModerateIn(BaseModel):
    action: str = Field(..., pattern="^(dismiss|hide)$")
    resolution: str = Field(..., min_length=2, max_length=500)
