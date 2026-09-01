"""Farmer model — extended profile for registered farmers."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Farmer(Base):
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    farmer_registration_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    aadhaar_last4: Mapped[str] = mapped_column(String(4), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")  # en, hi, gu
    village: Mapped[str] = mapped_column(String(120), nullable=True)
    district: Mapped[str] = mapped_column(String(80), nullable=True)
    state: Mapped[str] = mapped_column(String(80), nullable=True)
    land_area_acres: Mapped[float] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="farmer")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="farmer")
