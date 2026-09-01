"""Queue Token model — digital token assigned on arrival at the centre."""
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class TokenStatus(str, PyEnum):
    WAITING = "WAITING"
    CALLED = "CALLED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    NO_SHOW = "NO_SHOW"


class QueueToken(Base):
    __tablename__ = "queue_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    centre_id: Mapped[int] = mapped_column(ForeignKey("procurement_centres.id"), nullable=False, index=True)
    token_number: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # e.g. "A042"
    queue_position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[TokenStatus] = mapped_column(Enum(TokenStatus), default=TokenStatus.WAITING)
    estimated_wait_minutes: Mapped[float] = mapped_column(Float, default=0.0)
    arrival_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    called_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="queue_token")
