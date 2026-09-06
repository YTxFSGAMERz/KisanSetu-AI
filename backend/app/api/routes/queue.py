"""Queue management routes — officer controls and farmer live tracking."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, select
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
        select(QueueToken)
        .where(
            QueueToken.centre_id == centre_id,
            QueueToken.status.in_([TokenStatus.PROCESSING, TokenStatus.CALLED]),
        )
        .order_by(
            case((QueueToken.status == TokenStatus.PROCESSING, 1), else_=2),
            QueueToken.processing_start_time.desc().nullslast(),
            QueueToken.called_at.desc().nullslast(),
            QueueToken.id.desc(),
        )
        .limit(1)
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
    enriched_active = await _enrich_token(current_token, db) if current_token else None

    return QueueStatusResponse(
        centre_id=centre_id,
        current_token=current_token.token_number if current_token else None,
        active_token=enriched_active,
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
        raise HTTPException(status_code=400, detail="Token must be in WAITING or CALLED state to start processing")
    return await _enrich_token(token, db)


@router.post("/{token_id}/complete", response_model=QueueTokenResponse)
async def complete_token(
    token_id: int,
    current_user: User = Depends(require_role(*OFFICER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    token = await queue_service.complete_token(db, token_id)
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
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


@router.post("/add-farmers")
async def add_farmers(
    centre_id: int = Query(...),
    count: int = Query(10),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*OFFICER_ROLES)),
):
    """Add a fresh batch of farmers to the queue for testing/mandi operations."""
    from app.models.farmer import Farmer
    from app.models.crop import Crop
    from app.models.slot import Slot

    farmers_res = await db.execute(select(Farmer).limit(20))
    farmers = farmers_res.scalars().all()
    crops_res = await db.execute(select(Crop).limit(10))
    crops = crops_res.scalars().all()
    slot_res = await db.execute(select(Slot).where(Slot.centre_id == centre_id).limit(1))
    slot = slot_res.scalar_one_or_none()

    if not farmers or not crops or not slot:
        raise HTTPException(status_code=400, detail="Prerequisites not met")

    # Get current highest token number
    tokens_res = await db.execute(
        select(QueueToken.token_number).where(QueueToken.centre_id == centre_id)
    )
    existing_tokens = tokens_res.scalars().all()
    highest_num = 0
    import re
    for tn in existing_tokens:
        m = re.search(r'\d+', tn)
        if m:
            highest_num = max(highest_num, int(m.group(0)))

    waiting_res = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.centre_id == centre_id, QueueToken.status == TokenStatus.WAITING
        )
    )
    current_waiting = waiting_res.scalar() or 0

    added = []
    now = datetime.now(timezone.utc)
    for i in range(min(count, 20)):
        highest_num += 1
        tok_num = f"A{highest_num:03d}"
        farmer = farmers[(highest_num - 1) % len(farmers)]
        crop = crops[(highest_num - 1) % len(crops)]
        qty = [30.0, 35.0, 40.0, 45.0, 50.0][(highest_num - 1) % 5]

        bk = Booking(
            farmer_id=farmer.id,
            centre_id=centre_id,
            slot_id=slot.id,
            crop_id=crop.id,
            expected_quantity=qty,
            booking_number=f"BK-KNL-2026-{random.randint(1000, 9999)}",
            booking_status=BookingStatus.CONFIRMED,
            notes=f"{crop.name} {qty} Qtl",
            created_at=now,
        )
        db.add(bk)
        await db.flush()

        tok = QueueToken(
            booking_id=bk.id,
            centre_id=centre_id,
            token_number=tok_num,
            queue_position=current_waiting + i + 1,
            status=TokenStatus.WAITING,
            estimated_wait_minutes=(current_waiting + i + 1) * 15.0,
            arrival_time=now,
        )
        db.add(tok)
        await db.flush()
        added.append(tok_num)

    await queue_service._broadcast_queue_state(db, centre_id)
    return {"success": True, "added_tokens": added}


@router.post("/reset")
async def reset_queue(
    centre_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*OFFICER_ROLES)),
):
    """Reset all tokens for this centre back to WAITING."""
    await db.execute(
        update(QueueToken)
        .where(QueueToken.centre_id == centre_id)
        .values(status=TokenStatus.WAITING, called_at=None, processing_start_time=None, completed_at=None)
    )
    await db.commit()
    await queue_service._broadcast_queue_state(db, centre_id)
    return {"success": True, "message": "Queue reset to WAITING"}

