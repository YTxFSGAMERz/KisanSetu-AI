"""
Models package — import all models so SQLAlchemy registers them.
This file ensures all ORM classes are known to Base.metadata.
"""
from app.models.user import User, UserRole
from app.models.farmer import Farmer
from app.models.centre import ProcurementCentre
from app.models.crop import Crop
from app.models.slot import Slot, SlotStatus
from app.models.booking import Booking, BookingStatus
from app.models.queue_token import QueueToken, TokenStatus
from app.models.procurement import Procurement, ProcurementStatus, QualityGrade
from app.models.payment import Payment, PaymentStatus
from app.models.notification import Notification, NotificationType, NotificationChannel

__all__ = [
    "User", "UserRole",
    "Farmer",
    "ProcurementCentre",
    "Crop",
    "Slot", "SlotStatus",
    "Booking", "BookingStatus",
    "QueueToken", "TokenStatus",
    "Procurement", "ProcurementStatus", "QualityGrade",
    "Payment", "PaymentStatus",
    "Notification", "NotificationType", "NotificationChannel",
]
