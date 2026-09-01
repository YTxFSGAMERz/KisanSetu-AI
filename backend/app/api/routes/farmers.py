"""Farmer routes — profile, dashboard."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.farmer import Farmer
from app.models.booking import Booking, BookingStatus
from app.models.queue_token import QueueToken, TokenStatus
from app.models.payment import Payment, PaymentStatus
from app.models.notification import Notification
from app.models.procurement import Procurement
from app.schemas.farmer import FarmerResponse, FarmerUpdateRequest, FarmerDashboardResponse

router = APIRouter(prefix="/farmers", tags=["Farmers"])


async def _get_farmer(db: AsyncSession, user: User) -> Farmer:
    result = await db.execute(select(Farmer).where(Farmer.user_id == user.id))
    farmer = result.scalar_one_or_none()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return farmer


@router.get("/me", response_model=FarmerResponse)
async def get_my_farmer_profile(
    current_user: User = Depends(require_role(UserRole.FARMER)),
    db: AsyncSession = Depends(get_db),
):
    return await _get_farmer(db, current_user)


@router.put("/me", response_model=FarmerResponse)
async def update_my_farmer_profile(
    req: FarmerUpdateRequest,
    current_user: User = Depends(require_role(UserRole.FARMER)),
    db: AsyncSession = Depends(get_db),
):
    farmer = await _get_farmer(db, current_user)
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(farmer, field, value)
    await db.flush()
    return farmer


@router.get("/dashboard", response_model=FarmerDashboardResponse)
async def farmer_dashboard(
    current_user: User = Depends(require_role(UserRole.FARMER)),
    db: AsyncSession = Depends(get_db),
):
    farmer = await _get_farmer(db, current_user)

    # Active confirmed bookings
    active_bookings_result = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.farmer_id == farmer.id,
            Booking.booking_status == BookingStatus.CONFIRMED,
        )
    )
    active_count = active_bookings_result.scalar() or 0

    # Latest confirmed booking + slot info
    upcoming_slot = None
    current_token = None
    latest_booking_result = await db.execute(
        select(Booking)
        .where(Booking.farmer_id == farmer.id, Booking.booking_status == BookingStatus.CONFIRMED)
        .order_by(Booking.created_at.desc())
        .limit(1)
    )
    latest_booking = latest_booking_result.scalar_one_or_none()
    if latest_booking:
        from app.models.slot import Slot
        from app.models.centre import ProcurementCentre
        from app.models.crop import Crop

        slot_result = await db.execute(select(Slot).where(Slot.id == latest_booking.slot_id))
        slot = slot_result.scalar_one_or_none()
        centre_result = await db.execute(select(ProcurementCentre).where(ProcurementCentre.id == latest_booking.centre_id))
        centre = centre_result.scalar_one_or_none()
        crop_result = await db.execute(select(Crop).where(Crop.id == latest_booking.crop_id))
        crop = crop_result.scalar_one_or_none()

        if slot and centre and crop:
            upcoming_slot = {
                "booking_id": latest_booking.id,
                "booking_number": latest_booking.booking_number,
                "centre_name": centre.name,
                "slot_date": str(slot.slot_date),
                "start_time": str(slot.start_time),
                "end_time": str(slot.end_time),
                "crop_name": crop.name,
                "expected_quantity": latest_booking.expected_quantity,
            }

        # Queue token
        token_result = await db.execute(
            select(QueueToken).where(QueueToken.booking_id == latest_booking.id)
        )
        token = token_result.scalar_one_or_none()
        if token:
            # Farmers ahead in waiting
            ahead_result = await db.execute(
                select(func.count(QueueToken.id)).where(
                    QueueToken.centre_id == latest_booking.centre_id,
                    QueueToken.status == TokenStatus.WAITING,
                    QueueToken.queue_position < token.queue_position,
                )
            )
            farmers_ahead = ahead_result.scalar() or 0
            current_token = {
                "token_number": token.token_number,
                "queue_position": token.queue_position,
                "status": token.status.value,
                "estimated_wait_minutes": token.estimated_wait_minutes,
                "farmers_ahead": farmers_ahead,
            }

    # Recent procurements (last 5)
    proc_result = await db.execute(
        select(Procurement)
        .join(Booking, Procurement.booking_id == Booking.id)
        .where(Booking.farmer_id == farmer.id)
        .order_by(Procurement.created_at.desc())
        .limit(5)
    )
    recent_procs = []
    for proc in proc_result.scalars():
        recent_procs.append({
            "id": proc.id,
            "receipt_number": proc.receipt_number,
            "status": proc.status.value,
            "accepted_quantity": proc.accepted_quantity,
            "procurement_amount": proc.procurement_amount,
            "created_at": str(proc.created_at),
        })

    # Unread notifications
    unread_result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    unread_count = unread_result.scalar() or 0

    # Total payments received
    total_paid_result = await db.execute(
        select(func.sum(Payment.amount))
        .join(Procurement, Payment.procurement_id == Procurement.id)
        .join(Booking, Procurement.booking_id == Booking.id)
        .where(Booking.farmer_id == farmer.id, Payment.status == PaymentStatus.COMPLETED)
    )
    total_paid = total_paid_result.scalar() or 0.0

    return FarmerDashboardResponse(
        farmer=FarmerResponse.model_validate(farmer),
        active_bookings=active_count,
        upcoming_slot=upcoming_slot,
        current_token=current_token,
        recent_procurements=recent_procs,
        unread_notifications=unread_count,
        total_amount_received=float(total_paid),
    )
