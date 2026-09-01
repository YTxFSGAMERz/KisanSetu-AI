"""Booking model — farmer's appointment at a centre for a specific slot and crop."""
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class BookingStatus(str, PyEnum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False, index=True)
    centre_id: Mapped[int] = mapped_column(ForeignKey("procurement_centres.id"), nullable=False, index=True)
    slot_id: Mapped[int] = mapped_column(ForeignKey("slots.id"), nullable=False, index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), nullable=False)
    expected_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    booking_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    booking_status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.CONFIRMED)
    notes: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="bookings")
    centre: Mapped["ProcurementCentre"] = relationship("ProcurementCentre", back_populates="bookings")
    slot: Mapped["Slot"] = relationship("Slot", back_populates="bookings")
    crop: Mapped["Crop"] = relationship("Crop", back_populates="bookings")
    queue_token: Mapped["QueueToken"] = relationship("QueueToken", back_populates="booking", uselist=False)
    procurement: Mapped["Procurement"] = relationship("Procurement", back_populates="booking", uselist=False)
