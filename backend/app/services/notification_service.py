"""
Notification service — creates in-app notifications and sends real SMS via MSG91.
Falls back to simulation log if MSG91_AUTH_KEY is not configured.

MSG91 Setup (free tier: 100 SMS/day):
  1. Register at https://msg91.com
  2. Create a Flow template for OTP and booking
  3. Add to backend/.env:
     MSG91_AUTH_KEY=your_auth_key
     MSG91_OTP_TEMPLATE_ID=your_otp_template_id
     MSG91_BOOKING_TEMPLATE_ID=your_booking_template_id
     MSG91_PAYMENT_TEMPLATE_ID=your_payment_template_id
"""
import httpx
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.notification import Notification, NotificationType, NotificationChannel


# ─── MSG91 SMS Sender ─────────────────────────────────────────────────────────

async def _send_msg91_sms(phone: str, message: str, template_id: str = "") -> bool:
    """
    Send SMS via MSG91 Flow API.
    Returns True on success, False on failure (never raises — SMS is non-blocking).
    """
    auth_key = settings.MSG91_AUTH_KEY
    if not auth_key:
        # Graceful fallback: log to console if no API key configured
        print(f"[SMS] No MSG91_AUTH_KEY configured — simulating SMS to +91{phone}: {message[:100]}")
        return False

    # Normalize phone — MSG91 requires country code prefix
    normalized = phone.replace("+91", "").replace(" ", "").strip()
    mobile = f"91{normalized}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if template_id:
                # Use Flow API (template-based, DLT registered — required for India)
                payload = {
                    "template_id": template_id,
                    "recipients": [
                        {
                            "mobiles": mobile,
                            "VAR1": message[:40],   # Template variable 1
                        }
                    ],
                }
                resp = await client.post(
                    "https://api.msg91.com/api/v5/flow/",
                    headers={
                        "authkey": auth_key,
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
            else:
                # Fallback: transactional SMS (no template needed for testing)
                resp = await client.post(
                    "https://api.msg91.com/api/sendotp.php",
                    params={
                        "authkey": auth_key,
                        "mobile": mobile,
                        "message": message[:160],
                        "sender": settings.SMS_SENDER_ID or "KSTUAI",
                        "route": "4",  # Transactional route
                    },
                )

            if resp.status_code == 200:
                print(f"[SMS ✅] Sent to +91{normalized}")
                return True
            else:
                print(f"[SMS ❌] MSG91 error {resp.status_code}: {resp.text[:200]}")
                return False

    except Exception as e:
        print(f"[SMS ❌] Exception sending SMS: {e}")
        return False


async def send_otp_sms(phone: str, otp: str) -> bool:
    """Send OTP SMS via MSG91 OTP template."""
    message = f"KisanSetu: Your OTP is {otp}. Valid for 10 minutes. Do not share with anyone. - KSTUAI"
    return await _send_msg91_sms(phone, message, settings.MSG91_OTP_TEMPLATE_ID)


# ─── In-App Notification Creator ─────────────────────────────────────────────

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
    return notif


# ─── Pre-built Notification Templates ────────────────────────────────────────

async def notify_booking_confirmed(
    db: AsyncSession,
    user_id: int,
    booking_number: str,
    centre_name: str,
    slot_time: str,
    token_number: str,
    reference_id: int,
    phone: str | None = None,
):
    # In-app notification
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

    # Real SMS
    if phone:
        sms_body = (
            f"KisanSetu: Booking {booking_number} confirmed at {centre_name[:20]}. "
            f"Slot: {slot_time}. Token: {token_number}. - KSTUAI"
        )
        await _send_msg91_sms(phone, sms_body, settings.MSG91_BOOKING_TEMPLATE_ID)

    # Persist SMS notification record
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
    phone: str | None = None,
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
    if phone:
        sms_body = f"KisanSetu: Token {token_number} called at {centre_name[:20]}! Please go to counter NOW. - KSTUAI"
        await _send_msg91_sms(phone, sms_body, "")


async def notify_payment_completed(
    db: AsyncSession,
    user_id: int,
    amount: float,
    txn_ref: str,
    reference_id: int,
    phone: str | None = None,
):
    # In-app
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

    # Real SMS
    if phone:
        sms_body = f"KisanSetu: Rs.{amount:,.0f} paid to your bank a/c. Ref: {txn_ref}. - KSTUAI"
        await _send_msg91_sms(phone, sms_body, settings.MSG91_PAYMENT_TEMPLATE_ID)

    # SMS record
    await create_notification(
        db, user_id,
        title="KisanSetu: Payment Sent",
        message=f"KisanSetu: Rs.{amount:,.0f} paid. Ref: {txn_ref}.",
        notif_type=NotificationType.PAYMENT_COMPLETED,
        channel=NotificationChannel.SMS,
        reference_id=reference_id,
    )
