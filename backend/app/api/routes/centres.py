"""Centre routes — list centres and availability."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database.session import get_db
from app.models.centre import ProcurementCentre
from app.models.queue_token import QueueToken, TokenStatus
from app.models.slot import Slot, SlotStatus
from app.schemas.centre import CentreAvailabilityResponse, CentreResponse
from app.services.recommendation_engine import compute_congestion_score, congestion_label

router = APIRouter(prefix="/centres", tags=["Procurement Centres"])


@router.get("", response_model=list[CentreResponse])
async def list_centres(
    state: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    q = select(ProcurementCentre).where(ProcurementCentre.is_active == True)
    if state:
        q = q.where(ProcurementCentre.state.ilike(f"%{state}%"))
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/crops", tags=["Crops"])
async def list_crops(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    from app.models.crop import Crop
    result = await db.execute(select(Crop))
    crops = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "name_hi": c.name_hi,
            "name_gu": c.name_gu,
            "category": c.category,
            "unit": c.unit,
            "msp_per_quintal": c.msp_per_quintal,
            "processing_complexity": c.processing_complexity,
        }
        for c in crops
    ]


@router.get("/live-prices", tags=["Live Mandi Feed"])
async def get_live_mandi_prices(
    state: Optional[str] = Query(None),
    commodity: Optional[str] = Query(None),
    _=Depends(get_current_user),
):
    """Fetches real live Agmarknet / e-NAM mandi prices and arrival benchmarks."""
    from app.services.agmarknet_service import agmarknet_service
    return await agmarknet_service.fetch_live_mandi_prices(state=state, commodity=commodity)


@router.get("/{centre_id}", response_model=CentreResponse)
async def get_centre(
    centre_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    from fastapi import HTTPException
    result = await db.execute(
        select(ProcurementCentre).where(ProcurementCentre.id == centre_id)
    )
    centre = result.scalar_one_or_none()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    return centre


@router.get("/{centre_id}/availability", response_model=CentreAvailabilityResponse)
async def get_centre_availability(
    centre_id: int,
    date_str: Optional[str] = Query(None, alias="date", description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    from fastapi import HTTPException
    target_date = date.fromisoformat(date_str) if date_str else date.today()

    result = await db.execute(
        select(ProcurementCentre).where(ProcurementCentre.id == centre_id)
    )
    centre = result.scalar_one_or_none()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")

    # Count slots
    total_slots_result = await db.execute(
        select(func.count(Slot.id)).where(
            Slot.centre_id == centre_id,
            Slot.slot_date == target_date,
        )
    )
    open_slots_result = await db.execute(
        select(func.count(Slot.id)).where(
            Slot.centre_id == centre_id,
            Slot.slot_date == target_date,
            Slot.status == SlotStatus.OPEN,
        )
    )
    queue_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.centre_id == centre_id,
            QueueToken.status.in_([TokenStatus.WAITING, TokenStatus.CALLED]),
        )
    )

    total_slots = total_slots_result.scalar() or 0
    open_slots = open_slots_result.scalar() or 0
    active_queue = queue_result.scalar() or 0

    congestion = compute_congestion_score(
        booked_count=centre.daily_capacity - open_slots,
        slot_capacity=centre.daily_capacity,
        active_queue_length=active_queue,
        daily_target=centre.daily_capacity,
        avg_processing_minutes=centre.avg_processing_minutes,
    )

    return CentreAvailabilityResponse(
        centre=CentreResponse.model_validate(centre),
        date=str(target_date),
        available_slots=open_slots,
        total_slots=total_slots,
        congestion_score=congestion,
        congestion_label=congestion_label(congestion),
    )
