"""Pydantic schemas for Bookings."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.booking import BookingStatus


class BookingCreateRequest(BaseModel):
    centre_id: int
    slot_id: int
    crop_id: int
    expected_quantity: float
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    id: int
    booking_number: str
    farmer_id: int
    centre_id: int
    slot_id: int
    crop_id: int
    expected_quantity: float
    booking_status: BookingStatus
    notes: Optional[str] = None
    created_at: datetime
    # Enriched fields (joined)
    centre_name: Optional[str] = None
    slot_date: Optional[str] = None
    slot_start_time: Optional[str] = None
    crop_name: Optional[str] = None
    token_number: Optional[str] = None
    queue_position: Optional[int] = None

    model_config = {"from_attributes": True}
