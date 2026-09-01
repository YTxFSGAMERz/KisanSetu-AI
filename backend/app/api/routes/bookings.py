"""Booking routes — create, list, and cancel bookings."""
import random
import string
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.farmer import Farmer
from app.models.booking import Booking, BookingStatus
from app.models.slot import Slot, SlotStatus
from app.models.centre import ProcurementCentre
from app.models.crop import Crop
from app.schemas.booking import BookingCreateRequest, BookingResponse
from app.services import queue_service
from app.services import notification_service

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def _gen_booking_number(centre_code: str) -> str:
    suffix = "".join(random.choices(string.digits, k=6))
    return f"BK-{centre_code[:3].upper()}-{suffix}"


async def _enrich_booking(booking: Booking, db: AsyncSession) -> BookingResponse:
    slot_result = await db.execute(select(Slot).where(Slot.id == booking.slot_id))
    slot = slot_result.scalar_one_or_none()

    centre_result = await db.execute(select(ProcurementCentre).where(ProcurementCentre.id == booking.centre_id))
    centre = centre_result.scalar_one_or_none()

    crop_result = await db.execute(select(Crop).where(Crop.id == booking.crop_id))
    crop = crop_result.scalar_one_or_none()

    from app.models.queue_token import QueueToken
    token_result = await db.execute(select(QueueToken).where(QueueToken.booking_id == booking.id))
    token = token_result.scalar_one_or_none()

    return BookingResponse(
        id=booking.id,
        booking_number=booking.booking_number,
        farmer_id=booking.farmer_id,
        centre_id=booking.centre_id,
        slot_id=booking.slot_id,
        crop_id=booking.crop_id,
        expected_quantity=booking.expected_quantity,
        booking_status=booking.booking_status,
        notes=booking.notes,
        created_at=booking.created_at,
        centre_name=centre.name if centre else None,
        slot_date=str(slot.slot_date) if slot else None,
        slot_start_time=str(slot.start_time) if slot else None,
        crop_name=crop.name if crop else None,
        token_number=token.token_number if token else None,
        queue_position=token.queue_position if token else None,
    )


@router.post("", response_model=BookingResponse, status_code=201)
async def create_booking(
    req: BookingCreateRequest,
    current_user: User = Depends(require_role(UserRole.FARMER)),
    db: AsyncSession = Depends(get_db),
):
    # Get farmer profile
    farmer_result = await db.execute(select(Farmer).where(Farmer.user_id == current_user.id))
    farmer = farmer_result.scalar_one_or_none()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")

    # Verify slot exists and is open
    slot_result = await db.execute(select(Slot).where(Slot.id == req.slot_id))
    slot = slot_result.scalar_one_or_none()
    if not slot or slot.status != SlotStatus.OPEN:
        raise HTTPException(status_code=400, detail="Slot is not available")

    if slot.centre_id != req.centre_id:
        raise HTTPException(status_code=400, detail="Slot does not belong to the selected centre")

    # Check capacity — strict overbooking prevention
    if slot.booked_count >= slot.capacity:
        raise HTTPException(status_code=409, detail="Slot is fully booked")

    # Check farmer doesn't already have a booking for this slot
    dup_result = await db.execute(
        select(Booking).where(
            Booking.farmer_id == farmer.id,
            Booking.slot_id == req.slot_id,
            Booking.booking_status == BookingStatus.CONFIRMED,
        )
    )
    if dup_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="You already have a booking for this slot")

    # Get centre for booking number
    centre_result = await db.execute(select(ProcurementCentre).where(ProcurementCentre.id == req.centre_id))
    centre = centre_result.scalar_one_or_none()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")

    # Create booking
    booking = Booking(
        farmer_id=farmer.id,
        centre_id=req.centre_id,
        slot_id=req.slot_id,
        crop_id=req.crop_id,
        expected_quantity=req.expected_quantity,
        booking_number=_gen_booking_number(centre.code),
        notes=req.notes,
        booking_status=BookingStatus.CONFIRMED,
    )
    db.add(booking)
    slot.booked_count += 1
    if slot.booked_count >= slot.capacity:
        slot.status = SlotStatus.FULL

    await db.flush()

    # Generate queue token
    token = await queue_service.get_or_create_token(db, booking, req.centre_id)

    # Send notifications
    slot_time = f"{slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}"
    await notification_service.notify_booking_confirmed(
        db,
        user_id=current_user.id,
        booking_number=booking.booking_number,
        centre_name=centre.name,
        slot_time=slot_time,
        token_number=token.token_number,
        reference_id=booking.id,
    )

    return await _enrich_booking(booking, db)


@router.get("/my", response_model=list[BookingResponse])
async def my_bookings(
    current_user: User = Depends(require_role(UserRole.FARMER)),
    db: AsyncSession = Depends(get_db),
):
    farmer_result = await db.execute(select(Farmer).where(Farmer.user_id == current_user.id))
    farmer = farmer_result.scalar_one_or_none()
    if not farmer:
        return []

    result = await db.execute(
        select(Booking)
        .where(Booking.farmer_id == farmer.id)
        .order_by(Booking.created_at.desc())
    )
    bookings = result.scalars().all()
    return [await _enrich_booking(b, db) for b in bookings]


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # IDOR Protection: Farmers can only view their own bookings
    if current_user.role == UserRole.FARMER:
        farmer_result = await db.execute(select(Farmer).where(Farmer.user_id == current_user.id))
        farmer = farmer_result.scalar_one_or_none()
        if not farmer or booking.farmer_id != farmer.id:
            raise HTTPException(status_code=403, detail="Access denied to this booking")

    return await _enrich_booking(booking, db)


@router.put("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    current_user: User = Depends(require_role(UserRole.FARMER)),
    db: AsyncSession = Depends(get_db),
):
    farmer_result = await db.execute(select(Farmer).where(Farmer.user_id == current_user.id))
    farmer = farmer_result.scalar_one_or_none()

    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking or booking.farmer_id != (farmer.id if farmer else -1):
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.booking_status != BookingStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Only confirmed bookings can be cancelled")

    booking.booking_status = BookingStatus.CANCELLED

    # Release slot capacity
    slot_result = await db.execute(select(Slot).where(Slot.id == booking.slot_id))
    slot = slot_result.scalar_one_or_none()
    if slot and slot.booked_count > 0:
        slot.booked_count -= 1
        if slot.status == SlotStatus.FULL:
            slot.status = SlotStatus.OPEN

    await db.flush()
    return await _enrich_booking(booking, db)
