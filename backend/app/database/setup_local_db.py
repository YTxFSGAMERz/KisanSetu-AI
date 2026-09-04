"""
Setup complete, self-contained local SQLite database for KisanSetu AI.
Creates all 11 tables and seeds real Indian Mandis, MSP crops, 14-day slots,
demo users, farmer profiles, active queue tokens, bookings, procurements, and payments.

Run with: python -m app.database.setup_local_db
"""
import asyncio
from datetime import date, datetime, time, timedelta, timezone
from sqlalchemy import select

from app.core.security import hash_password
from app.database.session import AsyncSessionLocal, engine, Base
from app.models import (
    User, UserRole,
    Farmer,
    ProcurementCentre,
    Crop,
    Slot, SlotStatus,
    Booking, BookingStatus,
    QueueToken, TokenStatus,
    Procurement, ProcurementStatus, QualityGrade,
    Payment, PaymentStatus,
    Notification, NotificationType, NotificationChannel,
)
from app.database.real_india_mandi_data import REAL_INDIAN_MANDIS, REAL_CACP_CROPS


async def setup_local_database():
    print("🌾 Initializing KisanSetu AI Local SQLite Database...")

    # 1. Create all 11 relational tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ All 11 relational tables created successfully in SQLite.")

    async with AsyncSessionLocal() as session:
        # 2. Seed Real Government APMC Mandis
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
        print(f"✅ Synced {mandis_added} APMC Mandis across India.")

        # 3. Seed Official CACP Crops & MSP Rates
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
        print(f"✅ Synced {crops_added} Official CACP Crops & 2024-2026 MSP Rates.")

        # 4. Generate 14-Day Procurement Slots
        centres_result = await session.execute(
            select(ProcurementCentre).where(ProcurementCentre.is_active == True)
        )
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
                            booked_count=1 if day_offset == 0 and start_t == time(9, 0) else 0,
                            status=SlotStatus.OPEN,
                        )
                        session.add(slot)
                        slots_count += 1
        await session.flush()
        print(f"✅ Generated {slots_count} 14-day Procurement Slots across all Mandis.")

        # 5. Seed Core Demo Users
        users_data = [
            {
                "id": 1,
                "name": "Rajesh Verma (Kisan)",
                "phone": "9876543210",
                "email": "demo.farmer@example.com",
                "password_hash": hash_password("Farmer123!"),
                "role": UserRole.FARMER,
                "is_active": True,
            },
            {
                "id": 2,
                "name": "Anil Kumar (Mandi Officer)",
                "phone": "9876543211",
                "email": "demo.officer@example.com",
                "password_hash": hash_password("Officer123!"),
                "role": UserRole.PROCUREMENT_OFFICER,
                "is_active": True,
            },
            {
                "id": 3,
                "name": "Dr. Ramesh Sharma (Director, DoCA)",
                "phone": "9876543212",
                "email": "demo.admin@example.com",
                "password_hash": hash_password("Admin123!"),
                "role": UserRole.GOVERNMENT_ADMIN,
                "is_active": True,
            },
        ]

        users_added = 0
        for u in users_data:
            existing = await session.execute(select(User).where(User.id == u["id"]))
            if not existing.scalar_one_or_none():
                user_obj = User(**u)
                session.add(user_obj)
                users_added += 1
        await session.flush()
        print(f"✅ Seeded {users_added} Core Demo Users (Farmer, Officer, Admin).")

        # 6. Seed Farmer Profile for Rajesh Verma
        existing_farmer = await session.execute(select(Farmer).where(Farmer.user_id == 1))
        farmer = existing_farmer.scalar_one_or_none()
        if not farmer:
            farmer = Farmer(
                id=1,
                user_id=1,
                farmer_registration_number="FRN-HR-2026-0042",
                aadhaar_last4="9012",
                language="hi",
                village="Kachhwa",
                district="Karnal",
                state="Haryana",
                land_area_acres=12.5,
            )
            session.add(farmer)
            await session.flush()
            print("✅ Seeded Farmer profile for Rajesh Verma (FRN-HR-2026-0042).")

        # 7. Seed Sample Bookings
        first_mandi = centres[0] if centres else None
        first_slot_res = await session.execute(
            select(Slot).where(Slot.centre_id == first_mandi.id, Slot.slot_date == today).order_by(Slot.start_time)
        )
        first_slot = first_slot_res.scalars().first()

        existing_booking = await session.execute(select(Booking).where(Booking.id == 1))
        booking1 = existing_booking.scalar_one_or_none()
        if not booking1 and first_mandi and first_slot:
            booking1 = Booking(
                id=1,
                farmer_id=1,
                centre_id=first_mandi.id,
                slot_id=first_slot.id,
                crop_id=1,  # Wheat
                expected_quantity=40.0,
                booking_number="BK-KNL-2026-0001",
                booking_status=BookingStatus.CONFIRMED,
                notes="Wheat Sharbati grade FAQ, 40 Quintals",
            )
            session.add(booking1)
            await session.flush()

            # Seed Queue Token for Booking 1
            existing_token = await session.execute(select(QueueToken).where(QueueToken.booking_id == 1))
            if not existing_token.scalar_one_or_none():
                token1 = QueueToken(
                    id=1,
                    booking_id=1,
                    centre_id=first_mandi.id,
                    token_number="A001",
                    queue_position=1,
                    status=TokenStatus.WAITING,
                    estimated_wait_minutes=15.0,
                    arrival_time=datetime.now(timezone.utc) - timedelta(minutes=10),
                )
                session.add(token1)
                await session.flush()
                print("✅ Seeded Active Booking (BK-KNL-2026-0001) and Live Queue Token (A001).")

        # 8. Seed Sample Completed Procurement & DBT Payment
        existing_proc = await session.execute(select(Procurement).where(Procurement.id == 1))
        if not existing_proc.scalar_one_or_none() and booking1:
            proc1 = Procurement(
                id=1,
                booking_id=1,
                crop_id=1,
                expected_quantity=40.0,
                actual_quantity=40.0,
                accepted_quantity=38.5,
                rejected_quantity=1.5,
                quality_grade=QualityGrade.GRADE_A,
                procurement_amount=87587.50,
                status=ProcurementStatus.COMPLETED,
                processed_by=2,  # Anil Kumar (Officer)
                receipt_number="RCP-KNL-2026-0001",
                completed_at=datetime.now(timezone.utc) - timedelta(hours=2),
            )
            session.add(proc1)
            await session.flush()

            # Seed DBT Payment
            pay1 = Payment(
                id=1,
                procurement_id=1,
                amount=87587.50,
                status=PaymentStatus.COMPLETED,
                transaction_reference="TXN-DBT-2026-009182",
                bank_account_last4="1001",
                upi_id="rajeshverma@oksbi",
                completed_at=datetime.now(timezone.utc) - timedelta(hours=1),
                notes="Direct Benefit Transfer disbursed via PFMS / NPCI gateway",
            )
            session.add(pay1)
            await session.flush()
            print("✅ Seeded Completed Procurement Receipt (RCP-KNL-2026-0001) & DBT Payment.")

        # 9. Seed Notifications
        existing_notif = await session.execute(select(Notification).where(Notification.user_id == 1))
        if not existing_notif.scalars().first():
            notifs = [
                Notification(
                    id=1,
                    user_id=1,
                    title="Booking Confirmed ✅",
                    message="Your slot for Wheat at Karnal Grain Mandi has been confirmed. Token: A001",
                    type=NotificationType.BOOKING_CONFIRMED,
                    channel=NotificationChannel.IN_APP,
                    is_read=True,
                    reference_id=1,
                ),
                Notification(
                    id=2,
                    user_id=1,
                    title="Procurement Payment Disbursed 💰",
                    message="DBT payment of ₹87,587.50 has been transferred to your registered account ending in 1001.",
                    type=NotificationType.PAYMENT_COMPLETED,
                    channel=NotificationChannel.SMS,
                    is_read=False,
                    reference_id=1,
                ),
            ]
            session.add_all(notifs)
            await session.flush()
            print("✅ Seeded In-App and SMS Alerts.")

        await session.commit()

    print("\n🎉 Local SQLite Database Initialized & Fully Populated!")
    print("📍 File: backend/kisansetu.db")
    print("🚀 FastAPI backend can now run with 100% offline autonomy: uvicorn app.main:app --reload\n")


if __name__ == "__main__":
    asyncio.run(setup_local_database())
