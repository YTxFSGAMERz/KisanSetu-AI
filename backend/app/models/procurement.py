"""Procurement model — quality grading and quantity verification record."""
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class QualityGrade(str, PyEnum):
    GRADE_A = "GRADE_A"
    STANDARD = "STANDARD"
    BELOW_STANDARD = "BELOW_STANDARD"


class ProcurementStatus(str, PyEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class Procurement(Base):
    __tablename__ = "procurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), nullable=False)
    # Quantities in quintals
    expected_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    actual_quantity: Mapped[float] = mapped_column(Float, nullable=True)
    accepted_quantity: Mapped[float] = mapped_column(Float, nullable=True)
    rejected_quantity: Mapped[float] = mapped_column(Float, default=0.0)
    quality_grade: Mapped[QualityGrade] = mapped_column(Enum(QualityGrade), nullable=True)
    # MSP-based calculated amount ₹
    procurement_amount: Mapped[float] = mapped_column(Float, nullable=True)
    status: Mapped[ProcurementStatus] = mapped_column(Enum(ProcurementStatus), default=ProcurementStatus.PENDING)
    processed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    rejection_reason: Mapped[str] = mapped_column(String(400), nullable=True)
    receipt_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="procurement")
    crop: Mapped["Crop"] = relationship("Crop", back_populates="procurements")
    payment: Mapped["Payment"] = relationship("Payment", back_populates="procurement", uselist=False)
    officer: Mapped["User"] = relationship("User", foreign_keys=[processed_by])
