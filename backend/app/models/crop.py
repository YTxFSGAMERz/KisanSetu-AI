"""Crop model — supported crops with MSP and complexity data."""
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name_hi: Mapped[str] = mapped_column(String(80), nullable=True)   # Hindi name
    name_gu: Mapped[str] = mapped_column(String(80), nullable=True)   # Gujarati name
    category: Mapped[str] = mapped_column(String(80), nullable=False)  # cereal, oilseed, pulse, etc.
    unit: Mapped[str] = mapped_column(String(20), default="quintal")
    # MSP in ₹ per quintal (2026 rates)
    msp_per_quintal: Mapped[float] = mapped_column(Float, default=0.0)
    # Complexity factor for waiting-time calculation (1.0 = normal, >1 = slower to process)
    processing_complexity: Mapped[float] = mapped_column(Float, default=1.0)

    # Relationships
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="crop")
    procurements: Mapped[list["Procurement"]] = relationship("Procurement", back_populates="crop")
