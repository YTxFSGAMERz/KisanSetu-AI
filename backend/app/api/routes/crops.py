"""Crops routes — list available crops with MSP."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.crop import Crop

router = APIRouter(prefix="/crops", tags=["Crops"])

@router.get("")
async def list_crops(db: AsyncSession = Depends(get_db)):
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
