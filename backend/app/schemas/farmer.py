"""Pydantic schemas for Farmer profile."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator


class FarmerUpdateRequest(BaseModel):
    language: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    land_area_acres: Optional[float] = None
    aadhaar_last4: Optional[str] = None
    aadhaar_number: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_name: Optional[str] = None

    @field_validator("aadhaar_number", mode="before")
    @classmethod
    def validate_aadhaar(cls, v):
        if v is not None and not str(v).isdigit():
            raise ValueError("Aadhaar number must contain only digits")
        if v is not None and len(str(v)) != 12:
            raise ValueError("Aadhaar number must be exactly 12 digits")
        return v

    @field_validator("bank_ifsc", mode="before")
    @classmethod
    def validate_ifsc(cls, v):
        if v is not None and len(str(v)) != 11:
            raise ValueError("IFSC code must be exactly 11 characters")
        return v


class FarmerResponse(BaseModel):
    id: int
    user_id: int
    farmer_registration_number: str
    language: str
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    land_area_acres: Optional[float] = None
    # Bank fields (masked for security in real prod — show only last 4 digits)
    bank_account_number: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_name: Optional[str] = None
    # Aadhaar (last 4 only for display)
    aadhaar_last4: Optional[str] = None
    has_bank_account: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_fields(self):
        if self.bank_account_number:
            self.has_bank_account = True
            acct = str(self.bank_account_number)
            if not acct.startswith("*"):
                self.bank_account_number = f"{'*' * max(0, len(acct) - 4)}{acct[-4:]}" if len(acct) > 4 else acct
        return self


class FarmerDashboardResponse(BaseModel):
    farmer: FarmerResponse
    active_bookings: int
    upcoming_slot: Optional[dict] = None
    current_token: Optional[dict] = None
    recent_procurements: list[dict] = []
    unread_notifications: int = 0
    total_amount_received: float = 0.0
