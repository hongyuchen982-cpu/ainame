from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ExpertApplyIn(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=100)
    title: str = Field(..., min_length=2, max_length=120)
    specialties: str = Field("", max_length=500)
    bio: str = Field(..., min_length=20, max_length=3000)
    experience_years: int = Field(0, ge=0, le=80)
    portfolio: str = Field("", max_length=5000)


class ExpertReviewApplicationIn(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$")
    review_note: str = Field("", max_length=500)


class ExpertProfileOut(BaseModel):
    id: int
    user_id: int
    display_name: str
    title: str
    specialties: str
    bio: str
    experience_years: int
    portfolio: str
    status: str
    review_note: str
    rating_average: Decimal
    rating_count: int
    created_at: datetime
    reviewed_at: datetime | None


class AdminExpertProfileOut(ExpertProfileOut):
    username: str
    user_email: str


class ExpertPackageIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: str = Field(..., min_length=10, max_length=3000)
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    delivery_days: int = Field(..., ge=1, le=90)
    revision_count: int = Field(1, ge=0, le=20)


class ExpertPackageStatusIn(BaseModel):
    is_active: bool


class ExpertPackageOut(BaseModel):
    id: int
    expert_id: int
    expert_name: str
    expert_title: str
    expert_rating: Decimal
    expert_rating_count: int
    name: str
    description: str
    price: Decimal
    delivery_days: int
    revision_count: int
    is_active: bool
    created_at: datetime


class ExpertOrderCreateIn(BaseModel):
    package_id: int = Field(..., ge=1)
    project_id: int | None = Field(None, ge=1)
    requirement: str = Field(..., min_length=20, max_length=5000)
    client_request_id: str = Field(..., min_length=8, max_length=100)


class ExpertDeliveryIn(BaseModel):
    title: str = Field(..., min_length=2, max_length=160)
    content: str = Field(..., min_length=50, max_length=20000)
    attachment_url: str = Field("", max_length=500)


class ExpertReviewIn(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    content: str = Field("", max_length=1000)


class ExpertDeliveryOut(BaseModel):
    id: int
    title: str
    content: str
    attachment_url: str
    created_at: datetime


class ExpertReviewOut(BaseModel):
    id: int
    rating: int
    content: str
    created_at: datetime


class ExpertOrderOut(BaseModel):
    id: int
    order_no: str
    user_id: int
    customer_name: str
    expert_id: int
    expert_name: str
    package_id: int
    package_name: str
    project_id: int | None
    amount: Decimal
    requirement: str
    status: str
    created_at: datetime
    accepted_at: datetime | None
    delivered_at: datetime | None
    completed_at: datetime | None
    delivery: ExpertDeliveryOut | None
    review: ExpertReviewOut | None


class ExpertSettlementOut(BaseModel):
    id: int
    order_id: int
    order_no: str
    expert_id: int
    expert_name: str
    gross_amount: Decimal
    platform_fee: Decimal
    net_amount: Decimal
    status: str
    settled_at: datetime | None
    created_at: datetime
