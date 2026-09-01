"""Pydantic schemas for Slots and Recommendations."""
from datetime import date, time
from typing import Optional
from pydantic import BaseModel
from app.models.slot import SlotStatus


class SlotResponse(BaseModel):
    id: int
    centre_id: int
    centre_name: Optional[str] = None
    slot_date: date
    start_time: time
    end_time: time
    capacity: int
    booked_count: int
    available: int
    status: SlotStatus
    fill_percentage: float

    model_config = {"from_attributes": True}


class SlotRecommendation(BaseModel):
    slot: SlotResponse
    rank: int
    score: float               # Lower = better
    congestion_score: float    # 0-100
    congestion_label: str      # Low | Moderate | High | Very High
    estimated_wait_minutes: float
    reason: str                # Human-readable recommendation rationale


class SlotRecommendationsResponse(BaseModel):
    recommendations: list[SlotRecommendation]
    centre_id: int
    date: str
