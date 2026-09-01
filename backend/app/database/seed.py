"""
KisanSetu AI — Database Seed Script
Populates the database with realistic sample data for development and hackathon demo.
Run: python -m app.database.seed
"""
import asyncio
import random
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select

from app.database.session import AsyncSessionLocal, engine, Base
from app.core.config import settings
from app.core.security import hash_password
from app.models import (
    User, UserRole, Farmer, ProcurementCentre, Crop,
    Slot, SlotStatus, Booking, BookingStatus,
    QueueToken, TokenStatus, Procurement, ProcurementStatus, QualityGrade,
    Payment, PaymentStatus, Notification, NotificationType, NotificationChannel,
)

# ─── Realistic Indian Sample Data ──────────────────────────────────────────────

CENTRES_DATA = [
    {
        "name": "Karnal Grain Mandi — Central Procurement Hub",
        "code": "KGM-KNL-01",
        "address": "Near Old Bus Stand, Model Town, Karnal",
        "district": "Karnal",
        "state": "Haryana",
        "latitude": 29.6857,
        "longitude": 76.9905,
        "daily_capacity": 120,
        "processing_capacity": 6,
        "avg_processing_minutes": 18.0,
        "contact_phone": "0184-2234567",
    },
    {
        "name": "Nashik Onion & Grain Procurement Centre",
        "code": "NOGPC-NSK-02",
        "address": "Lasalgaon APMC Market Yard, Nashik",
        "district": "Nashik",
        "state": "Maharashtra",
        "latitude": 20.1938,
        "longitude": 74.0050,
        "daily_capacity": 90,
        "processing_capacity": 4,
        "avg_processing_minutes": 22.0,
        "contact_phone": "0253-2340987",
    },
    {
        "name": "Ludhiana Central Procurement Depot",
        "code": "LCPD-LDH-03",
        "address": "Gill Road, Mandi Board Complex, Ludhiana",
        "district": "Ludhiana",
        "state": "Punjab",
        "latitude": 30.9010,
        "longitude": 75.8573,
        "daily_capacity": 150,
        "processing_capacity": 8,
        "avg_processing_minutes": 15.0,
        "contact_phone": "0161-4543210",
    },
]

CROPS_DATA = [
    {"name": "Wheat", "name_hi": "गेहूँ", "name_gu": "ઘઉં", "category": "cereal", "msp_per_quintal": 2275.0, "processing_complexity": 1.0},
    {"name": "Paddy (Common)", "name_hi": "धान (सामान्य)", "name_gu": "ડાંગર (સામાન્ય)", "category": "cereal", "msp_per_quintal": 2300.0, "processing_complexity": 1.1},
    {"name": "Mustard", "name_hi": "सरसों", "name_gu": "સરસવ", "category": "oilseed", "msp_per_quintal": 5950.0, "processing_complexity": 1.2},
    {"name": "Gram (Chickpea)", "name_hi": "चना", "name_gu": "ચણા", "category": "pulse", "msp_per_quintal": 5440.0, "processing_complexity": 1.1},
    {"name": "Maize", "name_hi": "मक्का", "name_gu": "મકાઈ", "category": "cereal", "msp_per_quintal": 2090.0, "processing_complexity": 0.9},
]

FARMER_NAMES = [
    ("Ramesh Kumar Yadav", "ramesh.yadav@example.com", "9812341001", "Hisar", "Haryana"),
    ("Sukhwinder Singh", "sukhwinder.singh@example.com", "9878901002", "Patiala", "Punjab"),
    ("Prakash Narayan Patel", "prakash.patel@example.com", "9727801003", "Anand", "Gujarat"),
    ("Gurpreet Kaur Sandhu", "gurpreet.sandhu@example.com", "9815671004", "Amritsar", "Punjab"),
    ("Vijay Bhagwan Deshmukh", "vijay.deshmukh@example.com", "9823451005", "Pune", "Maharashtra"),
    ("Manjeet Singh Dhaliwal", "manjeet.dhaliwal@example.com", "9891231006", "Bathinda", "Punjab"),
    ("Harishchandra Lal Meena", "harishchandra.meena@example.com", "9983451007", "Jaipur", "Rajasthan"),
    ("Parvati Devi Choudhary", "parvati.choudhary@example.com", "9729871008", "Hisar", "Haryana"),
    ("Baldev Raj Arora", "baldev.arora@example.com", "9879001009", "Ludhiana", "Punjab"),
    ("Shantabai Kisanrao Patil", "shantabai.patil@example.com", "9822341010", "Nashik", "Maharashtra"),
    ("Tejpal Singh Beniwal", "tejpal.beniwal@example.com", "9680121011", "Sirsa", "Haryana"),
    ("Kamlavati Ramnarayan Sharma", "kamlavati.sharma@example.com", "9828901012", "Ajmer", "Rajasthan"),
    ("Amarjit Singh Bajwa", "amarjit.bajwa@example.com", "9876541013", "Ferozpur", "Punjab"),
    ("Nandini Krishnamurthy", "nandini.krishnamurthy@example.com", "9751231014", "Thanjavur", "Tamil Nadu"),
    ("Ranjit Kumar Mahato", "ranjit.mahato@example.com", "9934561015", "Ranchi", "Jharkhand"),
    ("Sunita Devi Yadav", "sunita.yadav@example.com", "9911231016", "Patna", "Bihar"),
    ("Jagdish Prasad Gupta", "jagdish.gupta@example.com", "9723451017", "Jhansi", "Uttar Pradesh"),
    ("Lalita Bai Thakur", "lalita.thakur@example.com", "9812901018", "Sagar", "Madhya Pradesh"),
    ("Hardev Singh Gill", "hardev.gill@example.com", "9870121019", "Moga", "Punjab"),
    ("Pushpabai Vithalrao Jadhav", "pushpabai.jadhav@example.com", "9923451020", "Kolhapur", "Maharashtra"),
]

VILLAGES = ["Rampura", "Kotla", "Nangal", "Majra", "Kheora", "Sultanpur", "Basant Nagar", "Sukhchain", "Ramgarh", "Bhalot"]


async def clear_tables(session):
    """Drop and recreate all tables cleanly."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables recreated")


async def seed_demo_accounts(session) -> dict:
    """Create demo accounts for farmer, officer, and admin roles using env credentials."""
    demos = {}

    farmer_pw = settings.DEMO_FARMER_PASSWORD or secrets.token_urlsafe(16)
    officer_pw = settings.DEMO_OFFICER_PASSWORD or secrets.token_urlsafe(16)
    admin_pw = settings.DEMO_ADMIN_PASSWORD or secrets.token_urlsafe(16)

    # Demo Farmer
    farmer_user = User(
        name="Demo Farmer (Rajesh Verma)",
        phone="9900000001",
        email=settings.DEMO_FARMER_EMAIL,
        password_hash=hash_password(farmer_pw),
        role=UserRole.FARMER,
    )
    session.add(farmer_user)
    await session.flush()
    demos["farmer_user"] = farmer_user

    farmer = Farmer(
        user_id=farmer_user.id,
        farmer_registration_number="FRN-HR-DEMO-001",
        aadhaar_last4="3421",
        language="hi",
        village="Gharaunda",
        district="Karnal",
        state="Haryana",
        land_area_acres=8.5,
    )
    session.add(farmer)

    # Demo Officer
    officer_user = User(
        name="Demo Officer (Arvind Sharma)",
        phone="9900000002",
        email=settings.DEMO_OFFICER_EMAIL,
        password_hash=hash_password(officer_pw),
        role=UserRole.PROCUREMENT_OFFICER,
    )
    session.add(officer_user)
    demos["officer_user"] = officer_user

    # Demo Admin
    admin_user = User(
        name="Demo Admin (Dr. Priya Mehta)",
        phone="9900000003",
        email=settings.DEMO_ADMIN_EMAIL,
        password_hash=hash_password(admin_pw),
        role=UserRole.GOVERNMENT_ADMIN,
    )
    session.add(admin_user)
    demos["admin_user"] = admin_user

    await session.flush()
    return demos


async def seed_centres(session) -> list:
    centres = []
    for data in CENTRES_DATA:
        c = ProcurementCentre(**data)
        session.add(c)
        centres.append(c)
    await session.flush()
    print(f"✅ Seeded {len(centres)} procurement centres")
    return centres


async def seed_crops(session) -> list:
    crops = []
    for data in CROPS_DATA:
        c = Crop(**data)
        session.add(c)
        crops.append(c)
    await session.flush()
    print(f"✅ Seeded {len(crops)} crops")
    return crops


async def seed_farmers(session) -> list:
    farmers_list = []
    for i, (name, email, phone, district, state) in enumerate(FARMER_NAMES, start=1):
        u = User(
            name=name,
            phone=phone,
            email=email,
            password_hash=hash_password(settings.DEMO_FARMER_PASSWORD or secrets.token_urlsafe(16)),
            role=UserRole.FARMER,
        )
        session.add(u)
        await session.flush()

        state_code = {"Haryana": "HR", "Punjab": "PB", "Gujarat": "GJ",
                      "Maharashtra": "MH", "Rajasthan": "RJ", "Bihar": "BR",
                      "Tamil Nadu": "TN", "Jharkhand": "JH", "Uttar Pradesh": "UP",
                      "Madhya Pradesh": "MP"}.get(state, "XX")
        frn = f"FRN-{state_code}-2026-{i:04d}"

        f = Farmer(
            user_id=u.id,
            farmer_registration_number=frn,
            aadhaar_last4=str(random.randint(1000, 9999)),
            language=random.choice(["en", "hi", "hi", "gu"]),
            village=random.choice(VILLAGES),
            district=district,
            state=state,
            land_area_acres=round(random.uniform(2.0, 25.0), 1),
        )
        session.add(f)
        await session.flush()
        farmers_list.append((u, f))

    print(f"✅ Seeded {len(farmers_list)} farmers")
    return farmers_list


async def seed_slots(session, centres: list) -> list:
    """Create slots for next 7 days at each centre with varied occupancy."""
    all_slots = []
    today = date.today()

    SLOT_WINDOWS = [
        (time(7, 0), time(9, 0)),
        (time(9, 0), time(11, 0)),
        (time(11, 0), time(13, 0)),
        (time(13, 0), time(15, 0)),
        (time(15, 0), time(17, 0)),
    ]

    for centre in centres:
        for day_offset in range(0, 7):
            slot_date = today + timedelta(days=day_offset)
            for start_t, end_t in SLOT_WINDOWS:
                cap = centre.processing_capacity * 4
                booked = random.randint(0, cap - 1)
                status = SlotStatus.OPEN if booked < cap else SlotStatus.FULL
                s = Slot(
                    centre_id=centre.id,
                    slot_date=slot_date,
                    start_time=start_t,
                    end_time=end_t,
                    capacity=cap,
                    booked_count=booked,
                    status=status,
                )
                session.add(s)
                all_slots.append(s)
    await session.flush()
    print(f"✅ Seeded {len(all_slots)} slots")
    return all_slots


async def seed_bookings_and_queue(
    session, demo_farmer: "Farmer", centres: list, crops: list, slots: list
) -> None:
    """Create bookings, queue tokens, procurements and payments for rich demo data."""
    today = date.today()

    # Find today's slots for centre 0 (Karnal)
    today_slots_karnal = [
        s for s in slots
        if s.centre_id == centres[0].id and s.slot_date == today
    ]
    if not today_slots_karnal:
        today_slots_karnal = slots[:3]

    demo_slot = today_slots_karnal[1]  # 9:00–11:00 slot

    # ── Booking for the DEMO farmer ───────────────────────────────────────────
    wheat = crops[0]
    demo_booking = Booking(
        farmer_id=demo_farmer.id,
        centre_id=centres[0].id,
        slot_id=demo_slot.id,
        crop_id=wheat.id,
        expected_quantity=50.0,
        booking_number="BK-KNL-2026-0001",
        booking_status=BookingStatus.CONFIRMED,
    )
    session.add(demo_booking)
    await session.flush()

    # Queue token A042 for the demo farmer
    demo_token = QueueToken(
        booking_id=demo_booking.id,
        centre_id=centres[0].id,
        token_number="A042",
        queue_position=42,
        status=TokenStatus.WAITING,
        estimated_wait_minutes=12.0,
        arrival_time=datetime.now(timezone.utc),
    )
    session.add(demo_token)

    # ── Generate 40 additional synthetic bookings with full lifecycle ─────────
    token_counters = {c.id: 1 for c in centres}

    for idx in range(1, 41):
        centre = random.choice(centres)
        crop = random.choice(crops)
        day_offset = random.randint(0, 3)
        centre_slots = [s for s in slots if s.centre_id == centre.id and s.slot_date == today + timedelta(days=day_offset)]
        if not centre_slots:
            continue
        slot = random.choice(centre_slots)

        bk_num = f"BK-{centre.code[:3]}-2026-{idx+1:04d}"
        qty = round(random.uniform(10.0, 100.0), 1)

        booking = Booking(
            farmer_id=demo_farmer.id,  # reuse demo farmer for simplicity
            centre_id=centre.id,
            slot_id=slot.id,
            crop_id=crop.id,
            expected_quantity=qty,
            booking_number=bk_num,
            booking_status=random.choice([
                BookingStatus.CONFIRMED, BookingStatus.CONFIRMED,
                BookingStatus.CONFIRMED, BookingStatus.COMPLETED,
                BookingStatus.NO_SHOW,
            ]),
        )
        session.add(booking)
        await session.flush()

        # Token
        token_num = f"A{token_counters[centre.id]:03d}"
        token_counters[centre.id] += 1
        is_past = day_offset == 0 and idx < 30
        tok_status = (
            TokenStatus.COMPLETED if is_past and random.random() > 0.15
            else TokenStatus.WAITING
        )

        tok = QueueToken(
            booking_id=booking.id,
            centre_id=centre.id,
            token_number=token_num,
            queue_position=token_counters[centre.id],
            status=tok_status,
            estimated_wait_minutes=round(random.uniform(5, 45), 1),
            arrival_time=datetime.now(timezone.utc) - timedelta(minutes=random.randint(5, 120)),
        )
        if tok_status in (TokenStatus.COMPLETED, TokenStatus.PROCESSING):
            tok.processing_start_time = datetime.now(timezone.utc) - timedelta(minutes=random.randint(10, 60))
        if tok_status == TokenStatus.COMPLETED:
            tok.completed_at = datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 30))

        session.add(tok)
        await session.flush()

        # Procurement for completed tokens
        if tok_status == TokenStatus.COMPLETED:
            accepted = round(qty * random.uniform(0.85, 1.0), 1)
            rejected = round(qty - accepted, 1)
            amount = accepted * crop.msp_per_quintal
            grade = random.choice(list(QualityGrade))
            receipt = f"RCP-DOCA-2026-{idx:05d}"

            proc = Procurement(
                booking_id=booking.id,
                crop_id=crop.id,
                expected_quantity=qty,
                actual_quantity=qty,
                accepted_quantity=accepted,
                rejected_quantity=rejected,
                quality_grade=grade,
                procurement_amount=amount,
                status=ProcurementStatus.COMPLETED,
                receipt_number=receipt,
                completed_at=tok.completed_at,
            )
            session.add(proc)
            await session.flush()

            pay_status = random.choice([
                PaymentStatus.COMPLETED, PaymentStatus.COMPLETED,
                PaymentStatus.PROCESSING, PaymentStatus.PENDING,
            ])
            txn = f"TXN-DOCA-2026-{idx:05d}" if pay_status == PaymentStatus.COMPLETED else None

            pay = Payment(
                procurement_id=proc.id,
                amount=amount,
                status=pay_status,
                transaction_reference=txn,
            )
            if pay_status == PaymentStatus.COMPLETED:
                pay.completed_at = tok.completed_at + timedelta(hours=random.randint(2, 48))
            session.add(pay)

    await session.flush()
    print("✅ Seeded bookings, queue tokens, procurements, and payments")


async def seed_notifications(session, demo_user_id: int) -> None:
    """Seed sample notifications for demo farmer."""
    notifs = [
        Notification(
            user_id=demo_user_id,
            title="Booking Confirmed ✅",
            message="Your slot for Wheat at Karnal Grain Mandi on today at 9:00 AM has been confirmed. Token: A042",
            type=NotificationType.BOOKING_CONFIRMED,
            channel=NotificationChannel.IN_APP,
            is_read=True,
        ),
        Notification(
            user_id=demo_user_id,
            title="Reminder: Slot in 2 Hours 🔔",
            message="Your procurement slot at Karnal Grain Mandi starts at 9:00 AM. Please arrive on time with your produce.",
            type=NotificationType.SLOT_REMINDER,
            channel=NotificationChannel.SMS,
            is_read=True,
        ),
        Notification(
            user_id=demo_user_id,
            title="3 Farmers Ahead in Queue",
            message="Token A039 is currently being processed. You are 3 positions away. Estimated wait: 12 minutes.",
            type=NotificationType.QUEUE_APPROACHING,
            channel=NotificationChannel.IN_APP,
            is_read=False,
        ),
    ]
    for n in notifs:
        session.add(n)
    print("✅ Seeded demo notifications")


async def run_seed():
    print("🌱 Starting KisanSetu AI database seed...")

    async with AsyncSessionLocal() as session:
        await clear_tables(session)

        # Seed core reference data
        centres = await seed_centres(session)
        crops = await seed_crops(session)

        # Demo accounts
        demos = await seed_demo_accounts(session)
        await session.flush()

        # Get demo farmer profile
        result = await session.execute(
            select(Farmer).where(Farmer.user_id == demos["farmer_user"].id)
        )
        demo_farmer = result.scalar_one()

        # Bulk farmers
        await seed_farmers(session)

        # Slots
        all_slots = await seed_slots(session, centres)

        # Bookings + queue + procurements + payments
        await seed_bookings_and_queue(session, demo_farmer, centres, crops, all_slots)

        # Notifications for demo farmer
        await seed_notifications(session, demos["farmer_user"].id)

        await session.commit()

    print("\n🎉 Seed complete! Demo accounts initialized:")
    print(f"  Farmer  → {settings.DEMO_FARMER_EMAIL}")
    print(f"  Officer → {settings.DEMO_OFFICER_EMAIL}")
    print(f"  Admin   → {settings.DEMO_ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(run_seed())
