"""Queue management routes — officer controls and farmer live tracking."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.queue_token import QueueToken, TokenStatus
from app.models.booking import Booking
from app.models.farmer import Farmer
from app.models.crop import Crop
from app.schemas.queue import QueueStatusResponse, QueueTokenResponse
from app.services import queue_service

router = APIRouter(prefix="/queue", tags=["Queue Management"])

OFFICER_ROLES = (UserRole.PROCUREMENT_OFFICER, UserRole.CENTRE_ADMIN, UserRole.GOVERNMENT_ADMIN)


async def _enrich_token(token: QueueToken, db: AsyncSession) -> QueueTokenResponse:
    booking_result = await db.execute(select(Booking).where(Booking.id == token.booking_id))
    booking = booking_result.scalar_one_or_none()

    farmer_name = None
    crop_name = None
    expected_qty = None

    if booking:
        farmer_result = await db.execute(select(Farmer).where(Farmer.id == booking.farmer_id))
        farmer = farmer_result.scalar_one_or_none()
        if farmer:
            user_result = await db.execute(
                select(User).where(User.id == farmer.user_id)
            )
            u = user_result.scalar_one_or_none()
            farmer_name = u.name if u else None

        crop_result = await db.execute(select(Crop).where(Crop.id == booking.crop_id))
        crop = crop_result.scalar_one_or_none()
        crop_name = crop.name if crop else None
        expected_qty = booking.expected_quantity

    # Farmers ahead
    ahead_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.centre_id == token.centre_id,
            QueueToken.status == TokenStatus.WAITING,
            QueueToken.queue_position < token.queue_position,
        )
    )
    farmers_ahead = ahead_result.scalar() or 0

    return QueueTokenResponse(
        id=token.id,
        booking_id=token.booking_id,
        centre_id=token.centre_id,
        token_number=token.token_number,
        queue_position=token.queue_position,
        status=token.status,
        estimated_wait_minutes=token.estimated_wait_minutes,
        arrival_time=token.arrival_time,
        called_at=token.called_at,
        processing_start_time=token.processing_start_time,
        completed_at=token.completed_at,
        farmer_name=farmer_name,
        crop_name=crop_name,
        expected_quantity=expected_qty,
        farmers_ahead=farmers_ahead,
    )


@router.get("/status", response_model=QueueStatusResponse)
async def get_queue_status(
    centre_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Get full queue state for a centre — used by officers and farmer live tracking."""
    from app.models.centre import ProcurementCentre
    centre_result = await db.execute(select(ProcurementCentre).where(ProcurementCentre.id == centre_id))
    centre = centre_result.scalar_one_or_none()

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
    no_show_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.centre_id == centre_id,
            QueueToken.status == TokenStatus.NO_SHOW,
        )
    )
    current_result = await db.execute(
        select(QueueToken).where(
            QueueToken.centre_id == centre_id,
            QueueToken.status.in_([TokenStatus.CALLED, TokenStatus.PROCESSING]),
        ).limit(1)
    )
    current_token = current_result.scalar_one_or_none()

    # Get WAITING queue (ordered by position)
    queue_result = await db.execute(
        select(QueueToken)
        .where(
            QueueToken.centre_id == centre_id,
            QueueToken.status == TokenStatus.WAITING,
        )
        .order_by(QueueToken.queue_position.asc())
        .limit(30)
    )
    waiting_tokens = queue_result.scalars().all()
    enriched_queue = [await _enrich_token(t, db) for t in waiting_tokens]

    return QueueStatusResponse(
        centre_id=centre_id,
        current_token=current_token.token_number if current_token else None,
        waiting_count=waiting_result.scalar() or 0,
        processing_count=processing_result.scalar() or 0,
        completed_today=completed_result.scalar() or 0,
        no_show_count=no_show_result.scalar() or 0,
        avg_processing_minutes=centre.avg_processing_minutes if centre else 20.0,
        estimated_wait_for_next=(centre.avg_processing_minutes if centre else 20.0),
        queue=enriched_queue,
    )


@router.get("/{booking_id}", response_model=QueueTokenResponse)
async def get_token_by_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(QueueToken).where(QueueToken.booking_id == booking_id)
    )
    token = result.scalar_one_or_none()
    if not token:
        raise HTTPException(status_code=404, detail="Queue token not found for this booking")

    # IDOR Protection: Farmers can only view queue token for their own bookings
    if current_user.role == UserRole.FARMER:
        booking_result = await db.execute(select(Booking).where(Booking.id == booking_id))
        booking = booking_result.scalar_one_or_none()
        farmer_result = await db.execute(select(Farmer).where(Farmer.user_id == current_user.id))
        farmer = farmer_result.scalar_one_or_none()
        if not booking or not farmer or booking.farmer_id != farmer.id:
            raise HTTPException(status_code=403, detail="Access denied to this queue token")

    return await _enrich_token(token, db)


@router.post("/call-next", response_model=QueueTokenResponse)
async def call_next_farmer(
    centre_id: int = Query(...),
    current_user: User = Depends(require_role(*OFFICER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    token = await queue_service.call_next_token(db, centre_id)
    if not token:
        raise HTTPException(status_code=404, detail="No farmers in queue")
    return await _enrich_token(token, db)


@router.post("/{token_id}/start", response_model=QueueTokenResponse)
async def start_procurement_for_token(
    token_id: int,
    current_user: User = Depends(require_role(*OFFICER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    token = await queue_service.start_processing(db, token_id)
    if not token:
        raise HTTPException(status_code=400, detail="Token must be in CALLED state to start processing")
    return await _enrich_token(token, db)


@router.post("/{token_id}/complete", response_model=QueueTokenResponse)
async def complete_token(
    token_id: int,
    current_user: User = Depends(require_role(*OFFICER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    token = await queue_service.complete_token(db, token_id)
    if not token:
        raise HTTPException(status_code=400, detail="Token must be in PROCESSING state to complete")
    return await _enrich_token(token, db)


@router.post("/{token_id}/skip", response_model=QueueTokenResponse)
async def skip_token(
    token_id: int,
    current_user: User = Depends(require_role(*OFFICER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    token = await queue_service.skip_token(db, token_id)
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    return await _enrich_token(token, db)


@router.post("/{token_id}/no-show", response_model=QueueTokenResponse)
async def mark_no_show(
    token_id: int,
    current_user: User = Depends(require_role(*OFFICER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    token = await queue_service.mark_no_show(db, token_id)
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    return await _enrich_token(token, db)
