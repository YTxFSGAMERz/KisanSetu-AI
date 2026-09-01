"""
Queue Management Service — token generation, state machine transitions,
and real-time WebSocket broadcast helpers.
"""
import random
import string
from datetime import date, datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.queue_token import QueueToken, TokenStatus
from app.models.slot import Slot
from app.core.websocket_manager import manager, QueueEvent


def generate_token_number(position: int) -> str:
    """Generate a memorable token like A042 (letter prefix + 3-digit number)."""
    prefix = "A"  # Could rotate B, C, etc. per counter
    return f"{prefix}{position:03d}"


async def get_or_create_token(
    db: AsyncSession, booking: Booking, centre_id: int
) -> QueueToken:
    """
    Issue a queue token for a booking if one doesn't already exist.
    Assigns the next available position at the centre.
    """
    # Check existing token
    result = await db.execute(
        select(QueueToken).where(QueueToken.booking_id == booking.id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    # Compute next position
    pos_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.centre_id == centre_id
        )
    )
    next_pos = (pos_result.scalar() or 0) + 1
    token_number = generate_token_number(next_pos)

    # Estimate wait time (simple: 20min × position / counters)
    from app.models.centre import ProcurementCentre
    centre_result = await db.execute(
        select(ProcurementCentre).where(ProcurementCentre.id == centre_id)
    )
    centre = centre_result.scalar_one_or_none()
    counters = (centre.processing_capacity if centre else 1) or 1
    avg_mins = centre.avg_processing_minutes if centre else 20.0

    # Only count WAITING tokens ahead in queue
    waiting_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.centre_id == centre_id,
            QueueToken.status == TokenStatus.WAITING,
        )
    )
    waiting_ahead = waiting_result.scalar() or 0
    estimated_wait = (waiting_ahead * avg_mins) / counters

    token = QueueToken(
        booking_id=booking.id,
        centre_id=centre_id,
        token_number=token_number,
        queue_position=next_pos,
        status=TokenStatus.WAITING,
        estimated_wait_minutes=round(estimated_wait, 1),
        arrival_time=datetime.now(timezone.utc),
    )
    db.add(token)
    await db.flush()
    return token


async def call_next_token(db: AsyncSession, centre_id: int) -> QueueToken | None:
    """Officer action: call the next WAITING token."""
    result = await db.execute(
        select(QueueToken)
        .where(
            QueueToken.centre_id == centre_id,
            QueueToken.status == TokenStatus.WAITING,
        )
        .order_by(QueueToken.queue_position.asc())
        .limit(1)
    )
    token = result.scalar_one_or_none()
    if not token:
        return None

    token.status = TokenStatus.CALLED
    token.called_at = datetime.now(timezone.utc)
    await db.flush()

    # Broadcast queue update
    await _broadcast_queue_state(db, centre_id)

    # Targeted notification to the specific farmer
    booking_result = await db.execute(
        select(Booking).where(Booking.id == token.booking_id)
    )
    booking = booking_result.scalar_one_or_none()
    if booking:
        farmer_user_id = booking.farmer.user_id if booking.farmer else None
        if farmer_user_id:
            await manager.send_to_user(
                farmer_user_id,
                QueueEvent.FARMER_CALLED,
                {
                    "token_number": token.token_number,
                    "message": f"🔔 Token {token.token_number} — Please proceed to the counter!",
                },
            )

    return token


async def start_processing(db: AsyncSession, token_id: int) -> QueueToken | None:
    result = await db.execute(select(QueueToken).where(QueueToken.id == token_id))
    token = result.scalar_one_or_none()
    if not token or token.status != TokenStatus.CALLED:
        return None
    token.status = TokenStatus.PROCESSING
    token.processing_start_time = datetime.now(timezone.utc)
    await db.flush()
    await _broadcast_queue_state(db, token.centre_id)
    return token


async def complete_token(db: AsyncSession, token_id: int) -> QueueToken | None:
    result = await db.execute(select(QueueToken).where(QueueToken.id == token_id))
    token = result.scalar_one_or_none()
    if not token or token.status != TokenStatus.PROCESSING:
        return None
    token.status = TokenStatus.COMPLETED
    token.completed_at = datetime.now(timezone.utc)

    # Mark booking as completed
    booking_result = await db.execute(select(Booking).where(Booking.id == token.booking_id))
    booking = booking_result.scalar_one_or_none()
    if booking:
        booking.booking_status = BookingStatus.COMPLETED

    await db.flush()
    await _broadcast_queue_state(db, token.centre_id)
    return token


async def skip_token(db: AsyncSession, token_id: int) -> QueueToken | None:
    result = await db.execute(select(QueueToken).where(QueueToken.id == token_id))
    token = result.scalar_one_or_none()
    if not token:
        return None
    token.status = TokenStatus.SKIPPED
    await db.flush()
    await _broadcast_queue_state(db, token.centre_id)
    return token


async def mark_no_show(db: AsyncSession, token_id: int) -> QueueToken | None:
    result = await db.execute(select(QueueToken).where(QueueToken.id == token_id))
    token = result.scalar_one_or_none()
    if not token:
        return None
    token.status = TokenStatus.NO_SHOW

    booking_result = await db.execute(select(Booking).where(Booking.id == token.booking_id))
    booking = booking_result.scalar_one_or_none()
    if booking:
        booking.booking_status = BookingStatus.NO_SHOW

    await db.flush()
    await _broadcast_queue_state(db, token.centre_id)
    return token


async def _broadcast_queue_state(db: AsyncSession, centre_id: int):
    """Compute current queue state and broadcast to all centre subscribers."""
    from app.models.centre import ProcurementCentre

    waiting_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.centre_id == centre_id,
            QueueToken.status == TokenStatus.WAITING,
        )
    )
    processing_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.centre_id == centre_id,
            QueueToken.status.in_([TokenStatus.CALLED, TokenStatus.PROCESSING]),
        )
    )
    completed_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.centre_id == centre_id,
            QueueToken.status == TokenStatus.COMPLETED,
        )
    )
    current_result = await db.execute(
        select(QueueToken).where(
            QueueToken.centre_id == centre_id,
            QueueToken.status.in_([TokenStatus.CALLED, TokenStatus.PROCESSING]),
        ).limit(1)
    )
    current_token = current_result.scalar_one_or_none()

    await manager.broadcast_to_centre(
        centre_id,
        QueueEvent.QUEUE_UPDATED,
        {
            "centre_id": centre_id,
            "waiting": waiting_result.scalar() or 0,
            "processing": processing_result.scalar() or 0,
            "completed": completed_result.scalar() or 0,
            "current_token": current_token.token_number if current_token else None,
        },
    )
