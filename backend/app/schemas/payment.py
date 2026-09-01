"""Pydantic schemas for Payments."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.payment import PaymentStatus


class PaymentResponse(BaseModel):
    id: int
    procurement_id: int
    amount: float
    status: PaymentStatus
    transaction_reference: Optional[str] = None
    initiated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    # Enriched
    crop_name: Optional[str] = None
    centre_name: Optional[str] = None
    receipt_number: Optional[str] = None

    model_config = {"from_attributes": True}


class PaymentProcessRequest(BaseModel):
    notes: Optional[str] = None
