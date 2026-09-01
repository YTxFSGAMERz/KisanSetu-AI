"""Pydantic schemas for Procurement Centres."""
from typing import Optional
from pydantic import BaseModel


class CentreResponse(BaseModel):
    id: int
    name: str
    code: str
    address: str
    district: str
    state: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    daily_capacity: int
    processing_capacity: int
    avg_processing_minutes: float
    is_active: bool
    contact_phone: Optional[str] = None

    model_config = {"from_attributes": True}


class CentreAvailabilityResponse(BaseModel):
    centre: CentreResponse
    date: str
    available_slots: int
    total_slots: int
    congestion_score: float
    congestion_label: str  # Low | Moderate | High | Very High
