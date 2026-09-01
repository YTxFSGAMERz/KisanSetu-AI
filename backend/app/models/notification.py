"""Notification model — in-app and simulated SMS alerts."""
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class NotificationType(str, PyEnum):
    BOOKING_CONFIRMED = "BOOKING_CONFIRMED"
    SLOT_REMINDER = "SLOT_REMINDER"
    QUEUE_APPROACHING = "QUEUE_APPROACHING"
    FARMER_CALLED = "FARMER_CALLED"
    PROCUREMENT_STARTED = "PROCUREMENT_STARTED"
    PROCUREMENT_COMPLETED = "PROCUREMENT_COMPLETED"
    PAYMENT_INITIATED = "PAYMENT_INITIATED"
    PAYMENT_COMPLETED = "PAYMENT_COMPLETED"
    GENERAL = "GENERAL"


class NotificationChannel(str, PyEnum):
    IN_APP = "IN_APP"
    SMS = "SMS"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), default=NotificationType.GENERAL)
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel), default=NotificationChannel.IN_APP)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    reference_id: Mapped[int] = mapped_column(Integer, nullable=True)  # booking/procurement/payment id
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
