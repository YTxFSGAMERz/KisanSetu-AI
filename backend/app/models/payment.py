"""Payment model — payment lifecycle tracking for procured produce."""
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class PaymentStatus(str, PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    procurement_id: Mapped[int] = mapped_column(ForeignKey("procurements.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_reference: Mapped[str] = mapped_column(String(50), nullable=True, unique=True)
    bank_account_last4: Mapped[str] = mapped_column(String(4), nullable=True)
    upi_id: Mapped[str] = mapped_column(String(80), nullable=True)
    initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    notes: Mapped[str] = mapped_column(String(300), nullable=True)

    # Relationships
    procurement: Mapped["Procurement"] = relationship("Procurement", back_populates="payment")
