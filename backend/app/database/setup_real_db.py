"""
Setup Real Production Government APMC Mandi and MSP Dataset.
Populates real Indian Mandis and official 2024-2026 CACP MSP crops into whatever database
is configured in DATABASE_URL (Supabase, Neon, PostgreSQL, SQLite).
Run: python -m app.database.setup_real_db
"""
import asyncio
from datetime import date, time, timedelta
from sqlalchemy import select

from app.database.session import AsyncSessionLocal, engine, Base
from app.models import ProcurementCentre, Crop, Slot, SlotStatus
from app.database.real_india_mandi_data import REAL_INDIAN_MANDIS, REAL_CACP_CROPS


async def seed_real_government_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Upsert Real Mandis
        mandis_added = 0
        for mandi in REAL_INDIAN_MANDIS:
            existing = await session.execute(
                select(ProcurementCentre).where(ProcurementCentre.code == mandi["code"])
            )
            if not existing.scalar_one_or_none():
                c = ProcurementCentre(**mandi)
                session.add(c)
                mandis_added += 1
        await session.flush()
        print(f"✅ Synced {mandis_added} Real APMC Mandis across India")

        # 2. Upsert Real CACP Crops with Official MSP Rates
        crops_added = 0
        for crop in REAL_CACP_CROPS:
            existing = await session.execute(
                select(Crop).where(Crop.name == crop["name"])
            )
            if not existing.scalar_one_or_none():
                c = Crop(**crop)
                session.add(c)
                crops_added += 1
        await session.flush()
        print(f"✅ Synced {crops_added} Real Official CACP Crops & 2024-2026 MSP Rates")

        # 3. Create Live Slots for the next 14 days for all active mandis
        centres_result = await session.execute(select(ProcurementCentre).where(ProcurementCentre.is_active == True))
        centres = centres_result.scalars().all()

        slot_templates = [
            (time(9, 0), time(11, 0)),
            (time(11, 0), time(13, 0)),
            (time(13, 0), time(15, 0)),
            (time(15, 0), time(17, 0)),
            (time(17, 0), time(19, 0)),
        ]

        today = date.today()
        slots_count = 0
        for centre in centres:
            for day_offset in range(14):
                slot_date = today + timedelta(days=day_offset)
                for start_t, end_t in slot_templates:
                    existing = await session.execute(
                        select(Slot).where(
                            Slot.centre_id == centre.id,
                            Slot.slot_date == slot_date,
                            Slot.start_time == start_t,
                        )
                    )
                    if not existing.scalar_one_or_none():
                        slot = Slot(
                            centre_id=centre.id,
                            slot_date=slot_date,
                            start_time=start_t,
                            end_time=end_t,
                            capacity=25,
                            booked_count=0,
                            status=SlotStatus.OPEN,
                        )
                        session.add(slot)
                        slots_count += 1

        await session.commit()
        print(f"✅ Generated {slots_count} 14-day Real Procurement Slots across all Mandis")
        print("\n🌾 Real Database Initialized Successfully!")


if __name__ == "__main__":
    asyncio.run(seed_real_government_data())
