"""Slot routes — list slots and smart recommendations."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database.session import get_db
from app.models.slot import Slot, SlotStatus
from app.models.centre import ProcurementCentre
from app.models.crop import Crop
from app.schemas.slot import SlotResponse, SlotRecommendation, SlotRecommendationsResponse
from app.services.recommendation_engine import get_slot_recommendations

router = APIRouter(prefix="/slots", tags=["Slots"])


def _enrich_slot(slot: Slot, centre_name: str = "") -> SlotResponse:
    avail = max(0, slot.capacity - slot.booked_count)
    fill_pct = round((slot.booked_count / max(slot.capacity, 1)) * 100, 1)
    return SlotResponse(
        id=slot.id,
        centre_id=slot.centre_id,
        centre_name=centre_name,
        slot_date=slot.slot_date,
        start_time=slot.start_time,
        end_time=slot.end_time,
        capacity=slot.capacity,
        booked_count=slot.booked_count,
        available=avail,
        status=slot.status,
        fill_percentage=fill_pct,
    )


@router.get("", response_model=list[SlotResponse])
async def list_slots(
    centre_id: Optional[int] = Query(None),
    date_str: Optional[str] = Query(None, alias="date"),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    q = select(Slot).where(Slot.status == SlotStatus.OPEN)
    if centre_id:
        q = q.where(Slot.centre_id == centre_id)
    if date_str:
        q = q.where(Slot.slot_date == date.fromisoformat(date_str))

    result = await db.execute(q.order_by(Slot.slot_date, Slot.start_time))
    slots = result.scalars().all()

    # Load centre names
    centre_ids = list({s.centre_id for s in slots})
    centre_map: dict[int, str] = {}
    if centre_ids:
        centres_result = await db.execute(
            select(ProcurementCentre).where(ProcurementCentre.id.in_(centre_ids))
        )
        for c in centres_result.scalars():
            centre_map[c.id] = c.name

    return [_enrich_slot(s, centre_map.get(s.centre_id, "")) for s in slots]


@router.get("/recommendations", response_model=SlotRecommendationsResponse)
async def get_recommendations(
    centre_id: int = Query(..., description="Procurement centre ID"),
    date_str: Optional[str] = Query(None, alias="date", description="YYYY-MM-DD (defaults to today)"),
    crop_id: Optional[int] = Query(None, description="Crop ID for complexity weighting"),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    target_date = date.fromisoformat(date_str) if date_str else date.today()

    crop_complexity = 1.0
    if crop_id:
        crop_result = await db.execute(select(Crop).where(Crop.id == crop_id))
        crop = crop_result.scalar_one_or_none()
        if crop:
            crop_complexity = crop.processing_complexity

    results = await get_slot_recommendations(
        db=db,
        centre_id=centre_id,
        target_date=target_date,
        crop_complexity=crop_complexity,
        top_n=3,
    )

    # Load centre name
    centre_result = await db.execute(select(ProcurementCentre).where(ProcurementCentre.id == centre_id))
    centre = centre_result.scalar_one_or_none()
    centre_name = centre.name if centre else ""

    recommendations = []
    for r in results:
        slot = r["slot"]
        slot_resp = _enrich_slot(slot, centre_name)
        recommendations.append(
            SlotRecommendation(
                slot=slot_resp,
                rank=r["rank"],
                score=r["score"],
                congestion_score=r["congestion_score"],
                congestion_label=r["congestion_label"],
                estimated_wait_minutes=r["estimated_wait_minutes"],
                reason=r["reason"],
            )
        )

    return SlotRecommendationsResponse(
        recommendations=recommendations,
        centre_id=centre_id,
        date=str(target_date),
    )
