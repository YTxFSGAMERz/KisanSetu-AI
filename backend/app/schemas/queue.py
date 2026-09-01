"""Pydantic schemas for Queue Tokens and Officer actions."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.queue_token import TokenStatus


class QueueTokenResponse(BaseModel):
    id: int
    booking_id: int
    centre_id: int
    token_number: str
    queue_position: int
    status: TokenStatus
    estimated_wait_minutes: float
    arrival_time: Optional[datetime] = None
    called_at: Optional[datetime] = None
    processing_start_time: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    # Enriched
    farmer_name: Optional[str] = None
    crop_name: Optional[str] = None
    expected_quantity: Optional[float] = None
    farmers_ahead: Optional[int] = None

    model_config = {"from_attributes": True}


class QueueStatusResponse(BaseModel):
    centre_id: int
    current_token: Optional[str] = None  # token number being processed
    waiting_count: int
    processing_count: int
    completed_today: int
    no_show_count: int
    avg_processing_minutes: float
    estimated_wait_for_next: float
    queue: list[QueueTokenResponse] = []
