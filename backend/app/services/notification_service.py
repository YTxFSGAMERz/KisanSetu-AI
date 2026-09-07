"""
Notification service — creates in-app notifications and dispatches real SMS.

SMS Providers (set SMS_PROVIDER in backend/.env):
  SIMULATED   — logs to console only (default/dev)
  ADB         — USB-connected Android phone via Termux:API (no cloud needed)
  MSG91       — MSG91 Flow API (India gov-preferred, free 100 SMS/day)

ADB Setup (one-time, ~2 min):
  1. Enable USB Debugging on Android phone
  2. Install Termux + Termux:API from F-Droid
  3. In Termux: pkg install termux-api
  4. Grant SMS permission to Termux:API when prompted
  5. Plug phone into PC via USB, authorize ADB on phone
  6. Set SMS_PROVIDER=ADB in backend/.env

MSG91 Setup (cloud alternative):
  1. Register at https://msg91.com
  2. Create Flow templates for OTP, booking, payment
  3. Set MSG91_AUTH_KEY + template IDs in backend/.env
"""
import logging
import subprocess
import httpx
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.notification import Notification, NotificationType, NotificationChannel

log = logging.getLogger(__name__)


# ─── ADB / Termux SMS Sender ──────────────────────────────────────────────────

async def _send_adb_sms(phone: str, message: str) -> bool:
    """
    Send SMS via Termux SMS Bridge running on USB-connected Android phone.
    Communication travels through the USB cable via adb port forwarding:
      PC backend -> http://127.0.0.1:8080/sms -> Phone Termux -> termux-sms-send.

    Returns True on success, False on any failure (never raises).
    """
    normalized = phone.replace("+91", "").replace(" ", "").strip()
    target = f"+91{normalized}"
    msg = message[:160]

    # Ensure port forward is active
    try:
        subprocess.run(["adb", "forward", "tcp:8080", "tcp:8080"], capture_output=True, timeout=5)
    except Exception:
        pass

    # Try fast, direct USB bridge to Termux
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "http://127.0.0.1:8080/sms",
                json={"phone": target, "message": msg},
            )
            if resp.status_code == 200:
                log.info("[SMS ✅] Termux/ADB bridge sent to %s", target)
                return True
            log.error("[SMS ❌] Termux bridge error (HTTP %d): %s", resp.status_code, resp.text[:200])
            return False
    except Exception as exc:
        log.warning("[SMS ⚠️] Termux bridge HTTP unavailable (%s), trying ADB shell fallback...", exc)

    # Fallback to direct ADB shell execution if bridge is temporarily stopped
    try:
        result = subprocess.run(
            ["adb", "shell", "termux-sms-send", "-n", target, msg],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode == 0:
            log.info("[SMS ✅] ADB/Termux fallback sent to %s", target)
            return True
        log.error("[SMS ❌] ADB error (rc=%d): %s", result.returncode, result.stderr.strip()[:200])
        return False
    except FileNotFoundError:
        log.error("[SMS ❌] 'adb' not found in PATH.")
        return False
    except subprocess.TimeoutExpired:
        log.error("[SMS ❌] ADB command timed out.")
        return False
    except Exception as exc:
        log.error("[SMS ❌] ADB unexpected exception: %s", exc)
        return False


# ─── MSG91 SMS Sender ─────────────────────────────────────────────────────────

async def _send_msg91_sms(phone: str, message: str, template_id: str = "") -> bool:
    """
    Send SMS via MSG91 Flow API.
    Returns True on success, False on failure (never raises — SMS is non-blocking).
    """
    auth_key = settings.MSG91_AUTH_KEY
    if not auth_key:
        log.warning("[SMS] No MSG91_AUTH_KEY configured — cannot send via MSG91.")
        return False

    normalized = phone.replace("+91", "").replace(" ", "").strip()
    mobile = f"91{normalized}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if template_id:
                # Flow API (template-based, DLT registered — required for India)
                payload = {
                    "template_id": template_id,
                    "recipients": [
                        {
                            "mobiles": mobile,
                            "VAR1": message[:40],
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
                # Transactional SMS (no template needed for testing)
                resp = await client.post(
                    "https://api.msg91.com/api/sendotp.php",
                    params={
                        "authkey": auth_key,
                        "mobile": mobile,
                        "message": message[:160],
                        "sender": settings.SMS_SENDER_ID or "KSTUAI",
                        "route": "4",
                    },
                )

            if resp.status_code == 200:
                log.info("[SMS ✅] MSG91 sent to +91%s", normalized)
                return True
            log.error("[SMS ❌] MSG91 error %d: %s", resp.status_code, resp.text[:200])
            return False

    except Exception as exc:
        log.error("[SMS ❌] MSG91 exception: %s", exc)
        return False


# ─── Unified SMS Dispatcher ───────────────────────────────────────────────────

async def send_sms(phone: str, message: str, template_id: str = "") -> bool:
    """
    Route SMS to the configured provider.
    Set SMS_PROVIDER in backend/.env:
      ADB        → USB Android phone via Termux (recommended for local dev)
      MSG91      → MSG91 cloud gateway (production)
      SIMULATED  → console log only (default)
    """
    if not phone:
        log.debug("[SMS] No phone number provided — skipping.")
        return False

    provider = (settings.SMS_PROVIDER or "SIMULATED").upper().strip()

    if provider == "ADB":
        return await _send_adb_sms(phone, message)

    if provider == "MSG91":
        return await _send_msg91_sms(phone, message, template_id)

    # SIMULATED or anything else
    log.info("[SMS SIM] To +91%s: %s", phone.replace("+91", "").strip(), message[:100])
    return False


# ─── OTP SMS ─────────────────────────────────────────────────────────────────

async def send_otp_sms(phone: str, otp: str) -> bool:
    """Send OTP SMS via the configured provider."""
    message = (
        f"KisanSetu: Your OTP is {otp}. "
        "Valid for 10 minutes. Do not share with anyone. - KSTUAI"
    )
    return await send_sms(phone, message, settings.MSG91_OTP_TEMPLATE_ID)


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

    # External SMS (ADB / MSG91 / SIMULATED based on SMS_PROVIDER)
    if phone:
        sms_body = (
            f"KisanSetu: Booking {booking_number} confirmed at {centre_name[:20]}. "
            f"Slot: {slot_time}. Token: {token_number}. - KSTUAI"
        )
        await send_sms(phone, sms_body, settings.MSG91_BOOKING_TEMPLATE_ID)

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
        sms_body = (
            f"KisanSetu: Token {token_number} called at {centre_name[:20]}! "
            "Please go to counter NOW. - KSTUAI"
        )
        await send_sms(phone, sms_body)


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

    # External SMS
    if phone:
        sms_body = f"KisanSetu: Rs.{amount:,.0f} paid to your bank a/c. Ref: {txn_ref}. - KSTUAI"
        await send_sms(phone, sms_body, settings.MSG91_PAYMENT_TEMPLATE_ID)

    # SMS record
    await create_notification(
        db, user_id,
        title="KisanSetu: Payment Sent",
        message=f"KisanSetu: Rs.{amount:,.0f} paid. Ref: {txn_ref}.",
        notif_type=NotificationType.PAYMENT_COMPLETED,
        channel=NotificationChannel.SMS,
        reference_id=reference_id,
    )
