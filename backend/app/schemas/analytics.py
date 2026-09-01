"""Pydantic schemas for Notifications and Analytics."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.notification import NotificationType, NotificationChannel


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: NotificationType
    channel: NotificationChannel
    is_read: bool
    reference_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MarkReadRequest(BaseModel):
    notification_ids: list[int]


# Analytics schemas
class CentreAnalytics(BaseModel):
    centre_id: int
    centre_name: str
    congestion_score: float
    farmers_today: int
    completed_today: int
    no_shows_today: int
    avg_processing_minutes: float
    total_quantity_kg: float
    total_amount: float


class AdminDashboardResponse(BaseModel):
    total_active_centres: int
    total_registered_farmers: int
    farmers_served_today: int
    avg_waiting_minutes: float
    total_procurement_quintals: float
    payment_completion_rate: float
    centres: list[CentreAnalytics]
    daily_volume_chart: list[dict]  # [{date, quantity, count}]
    no_show_rate: float


class OfficerDashboardResponse(BaseModel):
    centre_id: int
    centre_name: str
    expected_today: int
    currently_processing: int
    waiting: int
    completed: int
    no_shows: int
    avg_processing_minutes: float
    congestion_score: float
