"""Procurement Centre model — Mandi / APMC procurement locations."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class ProcurementCentre(Base):
    __tablename__ = "procurement_centres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(400), nullable=False)
    district: Mapped[str] = mapped_column(String(80), nullable=False)
    state: Mapped[str] = mapped_column(String(80), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    # Number of farmer arrivals that can be handled per day
    daily_capacity: Mapped[int] = mapped_column(Integer, default=100)
    # Simultaneous farmers that can be physically processed at counters
    processing_capacity: Mapped[int] = mapped_column(Integer, default=5)
    # Average minutes to process one farmer (base reference)
    avg_processing_minutes: Mapped[float] = mapped_column(Float, default=20.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    contact_phone: Mapped[str] = mapped_column(String(15), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    slots: Mapped[list["Slot"]] = relationship("Slot", back_populates="centre")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="centre")
