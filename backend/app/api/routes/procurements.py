"""Procurement routes — officer grading, digital receipt generation."""
import random
import string
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.booking import Booking
from app.models.centre import ProcurementCentre
from app.models.crop import Crop
from app.models.farmer import Farmer
from app.models.payment import Payment, PaymentStatus
from app.models.procurement import Procurement, ProcurementStatus
from app.schemas.procurement import (
    ProcurementCreateRequest,
    ProcurementResponse,
    ProcurementUpdateRequest,
)
from app.services import notification_service

router = APIRouter(prefix="/procurements", tags=["Procurements"])

OFFICER_ROLES = (UserRole.PROCUREMENT_OFFICER, UserRole.CENTRE_ADMIN, UserRole.GOVERNMENT_ADMIN)


def _gen_receipt() -> str:
    suffix = "".join(random.choices(string.digits, k=7))
    return f"RCP-DOCA-{suffix}"


async def _enrich_procurement(proc: Procurement, db: AsyncSession) -> ProcurementResponse:
    booking_result = await db.execute(select(Booking).where(Booking.id == proc.booking_id))
    booking = booking_result.scalar_one_or_none()

    centre_name = None
    farmer_name = None
    if booking:
        centre_result = await db.execute(select(ProcurementCentre).where(ProcurementCentre.id == booking.centre_id))
        centre = centre_result.scalar_one_or_none()
        centre_name = centre.name if centre else None

        farmer_result = await db.execute(select(Farmer).where(Farmer.id == booking.farmer_id))
        farmer = farmer_result.scalar_one_or_none()
        if farmer:
            user_result = await db.execute(select(User).where(User.id == farmer.user_id))
            u = user_result.scalar_one_or_none()
            farmer_name = u.name if u else None

    crop_result = await db.execute(select(Crop).where(Crop.id == proc.crop_id))
    crop = crop_result.scalar_one_or_none()

    return ProcurementResponse(
        id=proc.id,
        booking_id=proc.booking_id,
        crop_id=proc.crop_id,
        expected_quantity=proc.expected_quantity,
        actual_quantity=proc.actual_quantity,
        accepted_quantity=proc.accepted_quantity,
        rejected_quantity=proc.rejected_quantity or 0.0,
        quality_grade=proc.quality_grade,
        procurement_amount=proc.procurement_amount,
        status=proc.status,
        receipt_number=proc.receipt_number,
        created_at=proc.created_at,
        completed_at=proc.completed_at,
        crop_name=crop.name if crop else None,
        centre_name=centre_name,
        farmer_name=farmer_name,
        msp_per_quintal=crop.msp_per_quintal if crop else None,
    )


@router.post("", response_model=ProcurementResponse, status_code=201)
async def create_procurement(
    req: ProcurementCreateRequest,
    current_user: User = Depends(require_role(*OFFICER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    booking_result = await db.execute(select(Booking).where(Booking.id == req.booking_id))
    booking = booking_result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Prevent duplicate procurement
    existing_result = await db.execute(
        select(Procurement).where(Procurement.booking_id == req.booking_id)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Procurement record already exists for this booking")

    crop_result = await db.execute(select(Crop).where(Crop.id == booking.crop_id))
    crop = crop_result.scalar_one_or_none()
    msp = crop.msp_per_quintal if crop else 0.0

    amount = req.accepted_quantity * msp

    proc = Procurement(
        booking_id=req.booking_id,
        crop_id=booking.crop_id,
        expected_quantity=booking.expected_quantity,
        actual_quantity=req.actual_quantity,
        accepted_quantity=req.accepted_quantity,
        rejected_quantity=req.rejected_quantity,
        quality_grade=req.quality_grade,
        procurement_amount=amount,
        status=ProcurementStatus.IN_PROGRESS,
        processed_by=current_user.id,
        rejection_reason=req.rejection_reason,
        receipt_number=_gen_receipt(),
    )
    db.add(proc)
    await db.flush()

    # Auto-create PENDING payment record
    pay = Payment(
        procurement_id=proc.id,
        amount=amount,
        status=PaymentStatus.PENDING,
    )
    db.add(pay)
    await db.flush()

    return await _enrich_procurement(proc, db)


@router.get("/my", response_model=list[ProcurementResponse])
async def my_procurements(
    current_user: User = Depends(require_role(UserRole.FARMER)),
    db: AsyncSession = Depends(get_db),
):
    farmer_result = await db.execute(select(Farmer).where(Farmer.user_id == current_user.id))
    farmer = farmer_result.scalar_one_or_none()
    if not farmer:
        return []

    result = await db.execute(
        select(Procurement)
        .join(Booking, Procurement.booking_id == Booking.id)
        .where(Booking.farmer_id == farmer.id)
        .order_by(Procurement.created_at.desc())
    )
    return [await _enrich_procurement(p, db) for p in result.scalars()]


@router.get("/{procurement_id}", response_model=ProcurementResponse)
async def get_procurement(
    procurement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Procurement).where(Procurement.id == procurement_id))
    proc = result.scalar_one_or_none()
    if not proc:
        raise HTTPException(status_code=404, detail="Procurement not found")

    # IDOR Protection: Farmers can only view their own procurement records
    if current_user.role == UserRole.FARMER:
        booking_result = await db.execute(select(Booking).where(Booking.id == proc.booking_id))
        booking = booking_result.scalar_one_or_none()
        farmer_result = await db.execute(select(Farmer).where(Farmer.user_id == current_user.id))
        farmer = farmer_result.scalar_one_or_none()
        if not booking or not farmer or booking.farmer_id != farmer.id:
            raise HTTPException(status_code=403, detail="Access denied to this procurement record")

    return await _enrich_procurement(proc, db)


@router.put("/{procurement_id}", response_model=ProcurementResponse)
async def update_procurement(
    procurement_id: int,
    req: ProcurementUpdateRequest,
    current_user: User = Depends(require_role(*OFFICER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Procurement).where(Procurement.id == procurement_id))
    proc = result.scalar_one_or_none()
    if not proc:
        raise HTTPException(status_code=404, detail="Procurement not found")

    for field, value in req.model_dump(exclude_none=True).items():
        setattr(proc, field, value)

    if req.status == ProcurementStatus.COMPLETED:
        proc.completed_at = datetime.now(timezone.utc)

        # Update payment to PROCESSING
        pay_result = await db.execute(select(Payment).where(Payment.procurement_id == proc.id))
        pay = pay_result.scalar_one_or_none()
        if pay:
            pay.status = PaymentStatus.PROCESSING
            pay.initiated_at = datetime.now(timezone.utc)

        # Notify farmer
        booking_result = await db.execute(select(Booking).where(Booking.id == proc.booking_id))
        booking = booking_result.scalar_one_or_none()
        if booking:
            farmer_result = await db.execute(select(Farmer).where(Farmer.id == booking.farmer_id))
            farmer = farmer_result.scalar_one_or_none()
            if farmer:
                await notification_service.create_notification(
                    db,
                    user_id=farmer.user_id,
                    title="Procurement Completed ✅",
                    message=f"Your produce has been procured. Receipt: {proc.receipt_number}. Payment is being processed.",
                    notif_type=notification_service.NotificationType.PROCUREMENT_COMPLETED,
                    reference_id=proc.id,
                )

    await db.flush()
    return await _enrich_procurement(proc, db)
