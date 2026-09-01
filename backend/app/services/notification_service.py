"""
Notification service — creates in-app notifications and simulates SMS delivery.
Designed so real SMS providers (e.g., Twilio, MSG91) can be plugged in later.
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType, NotificationChannel


async def create_notification(
    db: AsyncSession,
    user_id: int,
    title: str,
    message: str,
    notif_type: NotificationType,
    channel: NotificationChannel = NotificationChannel.IN_APP,
    reference_id: int | None = None,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notif_type,
        channel=channel,
        reference_id=reference_id,
    )
    db.add(notif)
    await db.flush()

    # Simulate SMS log
    if channel == NotificationChannel.SMS:
        _simulate_sms(user_id, message)

    return notif


def _simulate_sms(user_id: int, message: str):
    """Prototype SMS simulation — logs instead of actually sending."""
    print(f"[SMS SIMULATOR] → User {user_id}: {message[:160]}")


# ─── Pre-built notification templates ────────────────────────────────────────

async def notify_booking_confirmed(
    db: AsyncSession,
    user_id: int,
    booking_number: str,
    centre_name: str,
    slot_time: str,
    token_number: str,
    reference_id: int,
):
    await create_notification(
        db, user_id,
        title="Booking Confirmed ✅",
        message=(
            f"Your booking {booking_number} at {centre_name} is confirmed. "
            f"Slot: {slot_time}. Your token: {token_number}."
        ),
        notif_type=NotificationType.BOOKING_CONFIRMED,
        channel=NotificationChannel.IN_APP,
        reference_id=reference_id,
    )
    # Also send SMS
    await create_notification(
        db, user_id,
        title="KisanSetu: Booking Confirmed",
        message=f"KisanSetu: Slot {slot_time} booked at {centre_name}. Token: {token_number}.",
        notif_type=NotificationType.BOOKING_CONFIRMED,
        channel=NotificationChannel.SMS,
        reference_id=reference_id,
    )


async def notify_farmer_called(
    db: AsyncSession,
    user_id: int,
    token_number: str,
    centre_name: str,
    reference_id: int,
):
    await create_notification(
        db, user_id,
        title=f"🔔 Token {token_number} — Please Proceed to Counter",
        message=(
            f"Your token {token_number} has been called at {centre_name}. "
            "Please come to the procurement counter immediately."
        ),
        notif_type=NotificationType.FARMER_CALLED,
        channel=NotificationChannel.IN_APP,
        reference_id=reference_id,
    )


async def notify_payment_completed(
    db: AsyncSession,
    user_id: int,
    amount: float,
    txn_ref: str,
    reference_id: int,
):
    await create_notification(
        db, user_id,
        title="Payment Transferred ₹ 💰",
        message=(
            f"₹{amount:,.0f} has been transferred to your registered bank account. "
            f"Transaction reference: {txn_ref}."
        ),
        notif_type=NotificationType.PAYMENT_COMPLETED,
        channel=NotificationChannel.IN_APP,
        reference_id=reference_id,
    )
    await create_notification(
        db, user_id,
        title="KisanSetu: Payment Sent",
        message=f"KisanSetu: Rs.{amount:,.0f} paid. Ref: {txn_ref}.",
        notif_type=NotificationType.PAYMENT_COMPLETED,
        channel=NotificationChannel.SMS,
        reference_id=reference_id,
    )
