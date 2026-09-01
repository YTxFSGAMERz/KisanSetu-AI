"""Payment routes — view and simulate payment processing."""
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
from app.models.booking import Booking
from app.models.procurement import Procurement
from app.models.payment import Payment, PaymentStatus
from app.models.crop import Crop
from app.models.centre import ProcurementCentre
from app.schemas.payment import PaymentResponse, PaymentProcessRequest
from app.services import notification_service

router = APIRouter(prefix="/payments", tags=["Payments"])

OFFICER_ROLES = (UserRole.PROCUREMENT_OFFICER, UserRole.CENTRE_ADMIN, UserRole.GOVERNMENT_ADMIN)


def _gen_txn_ref() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"TXN-DOCA-2026-{suffix}"


async def _enrich_payment(payment: Payment, db: AsyncSession) -> PaymentResponse:
    proc_result = await db.execute(select(Procurement).where(Procurement.id == payment.procurement_id))
    proc = proc_result.scalar_one_or_none()

    crop_name = None
    centre_name = None
    receipt_number = None
    if proc:
        crop_result = await db.execute(select(Crop).where(Crop.id == proc.crop_id))
        crop = crop_result.scalar_one_or_none()
        crop_name = crop.name if crop else None
        receipt_number = proc.receipt_number

        booking_result = await db.execute(select(Booking).where(Booking.id == proc.booking_id))
        booking = booking_result.scalar_one_or_none()
        if booking:
            centre_result = await db.execute(select(ProcurementCentre).where(ProcurementCentre.id == booking.centre_id))
            centre = centre_result.scalar_one_or_none()
            centre_name = centre.name if centre else None

    return PaymentResponse(
        id=payment.id,
        procurement_id=payment.procurement_id,
        amount=payment.amount,
        status=payment.status,
        transaction_reference=payment.transaction_reference,
        initiated_at=payment.initiated_at,
        completed_at=payment.completed_at,
        created_at=payment.created_at,
        crop_name=crop_name,
        centre_name=centre_name,
        receipt_number=receipt_number,
    )


@router.get("/my", response_model=list[PaymentResponse])
async def my_payments(
    current_user: User = Depends(require_role(UserRole.FARMER)),
    db: AsyncSession = Depends(get_db),
):
    farmer_result = await db.execute(select(Farmer).where(Farmer.user_id == current_user.id))
    farmer = farmer_result.scalar_one_or_none()
    if not farmer:
        return []

    result = await db.execute(
        select(Payment)
        .join(Procurement, Payment.procurement_id == Procurement.id)
        .join(Booking, Procurement.booking_id == Booking.id)
        .where(Booking.farmer_id == farmer.id)
        .order_by(Payment.created_at.desc())
    )
    return [await _enrich_payment(p, db) for p in result.scalars()]


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # IDOR Protection: Farmers can only view their own payments
    if current_user.role == UserRole.FARMER:
        proc_result = await db.execute(select(Procurement).where(Procurement.id == payment.procurement_id))
        proc = proc_result.scalar_one_or_none()
        if proc:
            booking_result = await db.execute(select(Booking).where(Booking.id == proc.booking_id))
            booking = booking_result.scalar_one_or_none()
            farmer_result = await db.execute(select(Farmer).where(Farmer.user_id == current_user.id))
            farmer = farmer_result.scalar_one_or_none()
            if not booking or not farmer or booking.farmer_id != farmer.id:
                raise HTTPException(status_code=403, detail="Access denied to this payment record")

    return await _enrich_payment(payment, db)


@router.post("/{payment_id}/process", response_model=PaymentResponse)
async def process_payment(
    payment_id: int,
    req: PaymentProcessRequest = PaymentProcessRequest(),
    current_user: User = Depends(require_role(*OFFICER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """
    Simulate payment processing (PENDING → PROCESSING → COMPLETED).
    In production, this would integrate with PFMS / Government payment gateway.
    """
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == PaymentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Payment is already completed")

    # Move to PROCESSING
    payment.status = PaymentStatus.PROCESSING
    payment.initiated_at = datetime.now(timezone.utc)
    payment.notes = req.notes
    await db.flush()

    # Immediately simulate completion (in production, this would be async via webhook)
    payment.status = PaymentStatus.COMPLETED
    payment.transaction_reference = _gen_txn_ref()
    payment.completed_at = datetime.now(timezone.utc)
    await db.flush()

    # Notify farmer
    proc_result = await db.execute(select(Procurement).where(Procurement.id == payment.procurement_id))
    proc = proc_result.scalar_one_or_none()
    if proc:
        booking_result = await db.execute(select(Booking).where(Booking.id == proc.booking_id))
        booking = booking_result.scalar_one_or_none()
        if booking:
            farmer_result = await db.execute(select(Farmer).where(Farmer.id == booking.farmer_id))
            farmer = farmer_result.scalar_one_or_none()
            if farmer:
                await notification_service.notify_payment_completed(
                    db,
                    user_id=farmer.user_id,
                    amount=payment.amount,
                    txn_ref=payment.transaction_reference,
                    reference_id=payment.id,
                )

    return await _enrich_payment(payment, db)
