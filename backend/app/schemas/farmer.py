"""Pydantic schemas for Farmer profile."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FarmerUpdateRequest(BaseModel):
    language: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    land_area_acres: Optional[float] = None
    aadhaar_last4: Optional[str] = None


class FarmerResponse(BaseModel):
    id: int
    user_id: int
    farmer_registration_number: str
    language: str
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    land_area_acres: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FarmerDashboardResponse(BaseModel):
    farmer: FarmerResponse
    active_bookings: int
    upcoming_slot: Optional[dict] = None
    current_token: Optional[dict] = None
    recent_procurements: list[dict] = []
    unread_notifications: int = 0
    total_amount_received: float = 0.0
