"""Slot model — time-bound appointment windows at a procurement centre."""
from datetime import date, datetime, time, timezone
from enum import Enum as PyEnum

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class SlotStatus(str, PyEnum):
    OPEN = "OPEN"
    FULL = "FULL"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class Slot(Base):
    __tablename__ = "slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    centre_id: Mapped[int] = mapped_column(ForeignKey("procurement_centres.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    booked_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[SlotStatus] = mapped_column(Enum(SlotStatus), default=SlotStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    centre: Mapped["ProcurementCentre"] = relationship("ProcurementCentre", back_populates="slots")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="slot")
