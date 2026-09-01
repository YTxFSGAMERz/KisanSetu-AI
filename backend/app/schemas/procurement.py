"""Pydantic schemas for Procurements."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.procurement import QualityGrade, ProcurementStatus


class ProcurementCreateRequest(BaseModel):
    booking_id: int
    actual_quantity: float
    accepted_quantity: float
    rejected_quantity: float = 0.0
    quality_grade: QualityGrade
    rejection_reason: Optional[str] = None


class ProcurementUpdateRequest(BaseModel):
    actual_quantity: Optional[float] = None
    accepted_quantity: Optional[float] = None
    rejected_quantity: Optional[float] = None
    quality_grade: Optional[QualityGrade] = None
    status: Optional[ProcurementStatus] = None
    rejection_reason: Optional[str] = None


class ProcurementResponse(BaseModel):
    id: int
    booking_id: int
    crop_id: int
    expected_quantity: float
    actual_quantity: Optional[float] = None
    accepted_quantity: Optional[float] = None
    rejected_quantity: float
    quality_grade: Optional[QualityGrade] = None
    procurement_amount: Optional[float] = None
    status: ProcurementStatus
    receipt_number: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    # Enriched
    crop_name: Optional[str] = None
    centre_name: Optional[str] = None
    farmer_name: Optional[str] = None
    msp_per_quintal: Optional[float] = None

    model_config = {"from_attributes": True}
