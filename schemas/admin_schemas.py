from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class AdminDashboardOut(BaseModel):
    users_total: int
    users_active: int
    projects_total: int
    projects_selected: int
    orders_total: int
    orders_pending: int
    paid_revenue: Decimal
    reports_total: int
    knowledge_files: int
    tasks_running: int


class AdminProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: str
    user_email: str
    title: str
    category: str
    status: str
    current_round: int
    final_name: str | None
    created_at: datetime
    updated_at: datetime
