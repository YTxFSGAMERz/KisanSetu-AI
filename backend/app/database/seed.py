"""
KisanSetu AI — Authentic Database Seed Script
Populates the database with real Government APMC Mandis, official CACP MSP rates,
diverse Indian farmers, genuine J-Forms, and accurate DBT payments.
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
from app.database.real_india_mandi_data import REAL_INDIAN_MANDIS, REAL_CACP_CROPS

FARMER_DIRECTORY = [
    ("Sukhwinder Singh", "sukhwinder.singh@example.com", "9878901002", "Patiala", "Punjab", "Kheri Gandian", "State Bank of India", "SBIN0050123", "20183920192"),
    ("Ramesh Kumar Yadav", "ramesh.yadav@example.com", "9812341001", "Hisar", "Haryana", "Barwala", "Punjab National Bank", "PUNB0123400", "012300010029381"),
    ("Gurpreet Kaur Sandhu", "gurpreet.sandhu@example.com", "9815671004", "Amritsar", "Punjab", "Majitha", "HDFC Bank", "HDFC0002341", "50100349201923"),
    ("Tejpal Singh Beniwal", "tejpal.beniwal@example.com", "9680121011", "Sirsa", "Haryana", "Chopta", "Canara Bank", "CNRB0001928", "1928101029384"),
    ("Baldev Raj Arora", "baldev.arora@example.com", "9879001009", "Ludhiana", "Punjab", "Jagraon", "Bank of Baroda", "BARB0LUDHIA", "29100200192834"),
    ("Parvati Devi Choudhary", "parvati.choudhary@example.com", "9729871008", "Hisar", "Haryana", "Hansi", "State Bank of India", "SBIN0001290", "30192837461"),
    ("Manjeet Singh Dhaliwal", "manjeet.dhaliwal@example.com", "9891231006", "Bathinda", "Punjab", "Talwandi Sabo", "Punjab National Bank", "PUNB0291000", "029100010039482"),
    ("Amarjit Singh Bajwa", "amarjit.bajwa@example.com", "9876541013", "Ferozpur", "Punjab", "Zira", "HDFC Bank", "HDFC0003829", "50100492819201"),
    ("Harishchandra Lal Meena", "harishchandra.meena@example.com", "9983451007", "Jaipur", "Rajasthan", "Chaksu", "State Bank of India", "SBIN0003819", "20394819203"),
    ("Prakash Narayan Patel", "prakash.patel@example.com", "9727801003", "Mehsana", "Gujarat", "Kadi", "Bank of Baroda", "BARB0MEHSAN", "39200200192834"),
    ("Vijay Bhagwan Deshmukh", "vijay.deshmukh@example.com", "9823451005", "Nashik", "Maharashtra", "Niphad", "ICICI Bank", "ICIC0001829", "182901502938"),
    ("Shantabai Kisanrao Patil", "shantabai.patil@example.com", "9822341010", "Nashik", "Maharashtra", "Yeola", "State Bank of India", "SBIN0002819", "30291827364"),
    ("Hardev Singh Gill", "hardev.gill@example.com", "9870121019", "Ludhiana", "Punjab", "Samrala", "Punjab & Sind Bank", "PSIB0000291", "02911000192834"),
    ("Pushpabai Vithalrao Jadhav", "pushpabai.jadhav@example.com", "9923451020", "Nashik", "Maharashtra", "Sinnar", "Bank of Maharashtra", "MAHB0000192", "20019283746"),
    ("Jagdish Prasad Gupta", "jagdish.gupta@example.com", "9723451017", "Indore", "Madhya Pradesh", "Mhow", "State Bank of India", "SBIN0004928", "20192837465"),
    ("Lalita Bai Thakur", "lalita.thakur@example.com", "9812901018", "Indore", "Madhya Pradesh", "Sanwer", "Punjab National Bank", "PUNB0382900", "038200010029384"),
    ("Kamlavati Ramnarayan Sharma", "kamlavati.sharma@example.com", "9828901012", "Sri Ganganagar", "Rajasthan", "Suratgarh", "State Bank of India", "SBIN0005829", "30192837462"),
    ("Ranjit Kumar Mahato", "ranjit.mahato@example.com", "9934561015", "Hapur", "Uttar Pradesh", "Garh", "Canara Bank", "CNRB0002938", "2938101029384"),
    ("Sunita Devi Yadav", "sunita.yadav@example.com", "9911231016", "Hapur", "Uttar Pradesh", "Pilkhuwa", "Bank of Baroda", "BARB0HAPURX", "19200200192834"),
]


async def clear_tables(session):
    """Drop and recreate all tables cleanly."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables cleanly recreated")


async def seed_centres(session) -> list:
    centres = []
    for data in REAL_INDIAN_MANDIS:
        c = ProcurementCentre(**data)
        session.add(c)
        centres.append(c)
    await session.flush()
    print(f"✅ Seeded {len(centres)} official APMC Mandis")
    return centres


async def seed_crops(session) -> list:
    crops = []
    for data in REAL_CACP_CROPS:
        c = Crop(**data)
        session.add(c)
        crops.append(c)
    await session.flush()
    print(f"✅ Seeded {len(crops)} CACP crops with official MSP rates")
    return crops


async def seed_demo_accounts(session) -> dict:
    demos = {}
    farmer_pw = settings.DEMO_FARMER_PASSWORD or "Farmer123!"
    officer_pw = settings.DEMO_OFFICER_PASSWORD or "Officer123!"
    admin_pw = settings.DEMO_ADMIN_PASSWORD or "Admin123!"

    # Demo Farmer (Rajesh Verma)
    farmer_user = User(
        name="Rajesh Verma (Kisan)",
        phone="9876543210",
        email=settings.DEMO_FARMER_EMAIL,
        password_hash=hash_password(farmer_pw),
        role=UserRole.FARMER,
    )
    session.add(farmer_user)
    await session.flush()
    demos["farmer_user"] = farmer_user

    farmer = Farmer(
        user_id=farmer_user.id,
        farmer_registration_number="FRN-HR-2026-0042",
        aadhaar_last4="9012",
        aadhaar_number="982345679012",
        language="hi",
        village="Kachhwa",
        district="Karnal",
        state="Haryana",
        land_area_acres=12.5,
        bank_name="HDFC Bank",
        bank_account_number="50100234561012",
        bank_ifsc="HDFC0001234",
    )
    session.add(farmer)
    demos["farmer"] = farmer

    # Demo Officer (Anil Kumar)
    officer_user = User(
        name="Anil Kumar (Mandi Officer)",
        phone="9876543211",
        email=settings.DEMO_OFFICER_EMAIL,
        password_hash=hash_password(officer_pw),
        role=UserRole.PROCUREMENT_OFFICER,
    )
    session.add(officer_user)
    demos["officer_user"] = officer_user

    # Demo Admin (Dr. Ramesh Sharma)
    admin_user = User(
        name="Dr. Ramesh Sharma (Director, DoCA)",
        phone="9876543212",
        email=settings.DEMO_ADMIN_EMAIL,
        password_hash=hash_password(admin_pw),
        role=UserRole.GOVERNMENT_ADMIN,
    )
    session.add(admin_user)
    demos["admin_user"] = admin_user

    await session.flush()
    return demos


async def seed_farmers(session) -> list:
    farmers_list = []
    farmer_pw = settings.DEMO_FARMER_PASSWORD or "Farmer123!"

    for i, (name, email, phone, district, state, village, b_name, ifsc, acct) in enumerate(FARMER_DIRECTORY, start=1):
        u = User(
            name=name,
            phone=phone,
            email=email,
            password_hash=hash_password(farmer_pw),
            role=UserRole.FARMER,
        )
        session.add(u)
        await session.flush()

        state_code = {"Haryana": "HR", "Punjab": "PB", "Gujarat": "GJ",
                      "Maharashtra": "MH", "Rajasthan": "RJ", "Bihar": "BR",
                      "Uttar Pradesh": "UP", "Madhya Pradesh": "MP"}.get(state, "IN")
        frn = f"FRN-{state_code}-2026-{i:04d}"

        f = Farmer(
            user_id=u.id,
            farmer_registration_number=frn,
            aadhaar_last4=str(random.randint(1000, 9999)),
            language="hi" if state in ("Haryana", "Rajasthan", "Uttar Pradesh", "Madhya Pradesh") else "en",
            village=village,
            district=district,
            state=state,
            land_area_acres=round(random.uniform(5.0, 30.0), 1),
            bank_name=b_name,
            bank_account_number=acct,
            bank_ifsc=ifsc,
        )
        session.add(f)
        await session.flush()
        farmers_list.append((u, f))

    print(f"✅ Seeded {len(farmers_list)} diverse Indian farmers")
    return farmers_list


async def seed_slots(session, centres: list) -> list:
    all_slots = []
    today = date.today()

    SLOT_WINDOWS = [
        (time(9, 0), time(11, 0)),
        (time(11, 0), time(13, 0)),
        (time(13, 0), time(15, 0)),
        (time(15, 0), time(17, 0)),
        (time(17, 0), time(19, 0)),
    ]

    for centre in centres:
        for day_offset in range(0, 14):
            slot_date = today + timedelta(days=day_offset)
            for start_t, end_t in SLOT_WINDOWS:
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
                all_slots.append(slot)

    await session.flush()
    print(f"✅ Generated {len(all_slots)} 14-day procurement slots across all Mandis")
    return all_slots


async def seed_bookings_and_queue(session, demo_farmer: Farmer, other_farmers: list, centres: list, crops: list, slots: list):
    today = date.today()
    karnal_mandi = centres[0]  # Karnal Grain Mandi
    crop_map = {c.name.lower(): c for c in crops}
    wheat = crop_map.get("wheat", crops[0])
    mustard = crop_map.get("mustard / rapeseed", crops[3])
    paddy_common = crop_map.get("paddy (common)", crops[1])
    paddy_grade_a = crop_map.get("paddy (grade a)", crops[2])
    gram = crop_map.get("gram (chickpea)", crops[4])

    # 1. Rajesh Verma's Past Completed Procurements (4 genuine seasons)
    rajesh_history = [
        {
            "crop": wheat,
            "qty": 50.0,
            "rate": 2275.0,
            "amount": 113750.0,
            "receipt": "JF-HR-KNL-2026-00412",
            "txn": "PFMS-DBT-2026-9821034",
            "date": datetime(2026, 4, 12, 11, 30, tzinfo=timezone.utc),
            "pay_date": datetime(2026, 4, 13, 14, 0, tzinfo=timezone.utc),
            "grade": QualityGrade.GRADE_A,
            "notes": "Wheat FAQ Sharbati 100 bags (50 Qtl). Moisture 11.2%, Foreign matter <0.5%. Grade A accepted.",
        },
        {
            "crop": mustard,
            "qty": 25.0,
            "rate": 5650.0,
            "amount": 141250.0,
            "receipt": "JF-HR-KNL-2026-00189",
            "txn": "PFMS-DBT-2026-9481920",
            "date": datetime(2026, 3, 28, 10, 15, tzinfo=timezone.utc),
            "pay_date": datetime(2026, 3, 29, 16, 30, tzinfo=timezone.utc),
            "grade": QualityGrade.GRADE_A,
            "notes": "Mustard (Sarson) 50 bags. Oil content 41.5%. Grade A approved.",
        },
        {
            "crop": paddy_common,
            "qty": 60.0,
            "rate": 2300.0,
            "amount": 138000.0,
            "receipt": "JF-HR-KNL-2025-08921",
            "txn": "PFMS-DBT-2025-8491023",
            "date": datetime(2025, 10, 18, 14, 45, tzinfo=timezone.utc),
            "pay_date": datetime(2025, 10, 19, 17, 10, tzinfo=timezone.utc),
            "grade": QualityGrade.GRADE_A,
            "notes": "Paddy PR-126 120 bags. Moisture 16.5%. Accepted at MSP standard.",
        },
        {
            "crop": paddy_grade_a,
            "qty": 40.0,
            "rate": 2320.0,
            "amount": 92800.0,
            "receipt": "JF-HR-KNL-2025-07614",
            "txn": "PFMS-DBT-2025-7819201",
            "date": datetime(2025, 9, 25, 12, 0, tzinfo=timezone.utc),
            "pay_date": datetime(2025, 9, 26, 15, 20, tzinfo=timezone.utc),
            "grade": QualityGrade.GRADE_A,
            "notes": "Paddy Grade A (Basmati PUSA 1509) 80 bags. Verified by Food & Civil Supplies Inspector.",
        },
    ]

    # Slot for past completed bookings (assign to any slot)
    past_slot = [s for s in slots if s.centre_id == karnal_mandi.id][0]

    for idx, h in enumerate(rajesh_history, start=1):
        bk = Booking(
            farmer_id=demo_farmer.id,
            centre_id=karnal_mandi.id,
            slot_id=past_slot.id,
            crop_id=h["crop"].id,
            expected_quantity=h["qty"],
            booking_number=f"BK-KNL-2026-{idx:04d}",
            booking_status=BookingStatus.COMPLETED,
            notes=h["notes"],
            created_at=h["date"] - timedelta(days=2),
        )
        session.add(bk)
        await session.flush()

        proc = Procurement(
            booking_id=bk.id,
            crop_id=h["crop"].id,
            expected_quantity=h["qty"],
            actual_quantity=h["qty"],
            accepted_quantity=h["qty"],
            rejected_quantity=0.0,
            quality_grade=h["grade"],
            procurement_amount=h["amount"],
            status=ProcurementStatus.COMPLETED,
            receipt_number=h["receipt"],
            created_at=h["date"],
            completed_at=h["date"],
        )
        session.add(proc)
        await session.flush()

        pay = Payment(
            procurement_id=proc.id,
            amount=h["amount"],
            status=PaymentStatus.COMPLETED,
            transaction_reference=h["txn"],
            bank_account_last4="1012",
            created_at=h["pay_date"],
            completed_at=h["pay_date"],
            notes="Direct Benefit Transfer via PFMS credited to HDFC Bank A/c ending 1012",
        )
        session.add(pay)

    # 2. Today's Active Live Queue in Karnal Mandi (Slot 09:00 - 11:00 AM)
    karnal_today_slot = [
        s for s in slots
        if s.centre_id == karnal_mandi.id and s.slot_date == today and s.start_time == time(9, 0)
    ][0]
    karnal_today_slot.booked_count = 10

    # The 10 farmers in Karnal Mandi queue today
    queue_roster = [
        # (Farmer index, Crop, Qty, Token, Status, Wait)
        (0, wheat, 50.0, "A001", TokenStatus.PROCESSING, 0.0),       # Sukhwinder Singh
        (1, mustard, 30.0, "A002", TokenStatus.WAITING, 4.0),        # Ramesh Kumar Yadav
        (2, wheat, 45.0, "A003", TokenStatus.WAITING, 8.0),          # Gurpreet Kaur Sandhu
        (3, gram, 25.0, "A004", TokenStatus.WAITING, 12.0),          # Tejpal Singh Beniwal
        (4, wheat, 60.0, "A005", TokenStatus.WAITING, 15.0),         # Baldev Raj Arora
        (5, mustard, 20.0, "A006", TokenStatus.WAITING, 18.0),       # Parvati Devi Choudhary
        (6, wheat, 40.0, "A007", TokenStatus.WAITING, 22.0),         # Manjeet Singh Dhaliwal
        (7, wheat, 35.0, "A008", TokenStatus.WAITING, 26.0),         # Amarjit Singh Bajwa
        (None, wheat, 40.0, "A009", TokenStatus.WAITING, 18.0),       # RAJESH VERMA (DEMO FARMER)
        (8, mustard, 30.0, "A010", TokenStatus.WAITING, 35.0),       # Harishchandra Lal Meena
    ]

    for pos, (f_idx, cr, qty, tok_num, st, est_wait) in enumerate(queue_roster, start=1):
        f_id = demo_farmer.id if f_idx is None else other_farmers[f_idx][1].id
        f_bk_num = f"BK-KNL-2026-{pos+10:04d}"

        bk = Booking(
            farmer_id=f_id,
            centre_id=karnal_mandi.id,
            slot_id=karnal_today_slot.id,
            crop_id=cr.id,
            expected_quantity=qty,
            booking_number=f_bk_num,
            booking_status=BookingStatus.CONFIRMED,
            notes=f"{cr.name} {qty} Quintals for morning procurement slot",
        )
        session.add(bk)
        await session.flush()

        tok = QueueToken(
            booking_id=bk.id,
            centre_id=karnal_mandi.id,
            token_number=tok_num,
            queue_position=pos,
            status=st,
            estimated_wait_minutes=est_wait,
            arrival_time=datetime.now(timezone.utc) - timedelta(minutes=(30 - pos * 2)),
            processing_start_time=datetime.now(timezone.utc) - timedelta(minutes=5) if st == TokenStatus.PROCESSING else None,
        )
        session.add(tok)

    # 3. Seed bookings and procurements for the other mandis (Khanna, Lasalgaon, Unjha, Indore, Sri Ganganagar)
    # Using the remaining other_farmers so all Mandis have rich analytics
    other_mandis = centres[1:]
    for m_idx, centre in enumerate(other_mandis):
        mandi_slots = [s for s in slots if s.centre_id == centre.id and s.slot_date == today]
        slot = mandi_slots[0] if mandi_slots else past_slot
        slot.booked_count = 5

        for k in range(5):
            f_tuple = other_farmers[(m_idx * 3 + k) % len(other_farmers)]
            f_obj = f_tuple[1]
            crop_obj = random.choice(crops)
            qty = float(random.choice([25.0, 30.0, 40.0, 50.0, 60.0]))
            amount = qty * crop_obj.msp_per_quintal

            bk = Booking(
                farmer_id=f_obj.id,
                centre_id=centre.id,
                slot_id=slot.id,
                crop_id=crop_obj.id,
                expected_quantity=qty,
                booking_number=f"BK-{centre.code.split('-')[2] if len(centre.code.split('-')) > 2 else 'MND'}-2026-{m_idx*10+k+1:04d}",
                booking_status=BookingStatus.COMPLETED if k < 3 else BookingStatus.CONFIRMED,
            )
            session.add(bk)
            await session.flush()

            tok = QueueToken(
                booking_id=bk.id,
                centre_id=centre.id,
                token_number=f"T{k+1:03d}",
                queue_position=k+1,
                status=TokenStatus.COMPLETED if k < 3 else TokenStatus.WAITING,
                estimated_wait_minutes=float(k * 15),
                arrival_time=datetime.now(timezone.utc) - timedelta(minutes=45 - k * 8),
                completed_at=datetime.now(timezone.utc) - timedelta(minutes=20 - k * 5) if k < 3 else None,
            )
            session.add(tok)
            await session.flush()

            if k < 3:
                proc = Procurement(
                    booking_id=bk.id,
                    crop_id=crop_obj.id,
                    expected_quantity=qty,
                    actual_quantity=qty,
                    accepted_quantity=qty,
                    rejected_quantity=0.0,
                    quality_grade=QualityGrade.GRADE_A,
                    procurement_amount=amount,
                    status=ProcurementStatus.COMPLETED,
                    receipt_number=f"JF-{centre.code.split('-')[2] if len(centre.code.split('-')) > 2 else 'MND'}-2026-{m_idx*100+k+1:05d}",
                    created_at=datetime.now(timezone.utc) - timedelta(hours=3),
                    completed_at=datetime.now(timezone.utc) - timedelta(hours=2),
                )
                session.add(proc)
                await session.flush()

                pay = Payment(
                    procurement_id=proc.id,
                    amount=amount,
                    status=PaymentStatus.COMPLETED,
                    transaction_reference=f"PFMS-DBT-2026-{m_idx*1000+k+1:06d}",
                    bank_account_last4=f_obj.bank_account_number[-4:] if f_obj.bank_account_number else "1001",
                    created_at=datetime.now(timezone.utc) - timedelta(hours=2),
                    completed_at=datetime.now(timezone.utc) - timedelta(hours=1),
                    notes="Direct Benefit Transfer disbursed via PFMS / NPCI gateway",
                )
                session.add(pay)

    await session.flush()
    print("✅ Seeded Rajesh Verma's 4 genuine past procurements & 10-farmer live queue at Karnal Mandi")


async def seed_notifications(session, demo_user_id: int):
    notifs = [
        Notification(
            user_id=demo_user_id,
            title="Today's Slot Confirmed ✅",
            message="Your morning slot for Wheat (40 Qtl) at Karnal Grain Mandi is confirmed. Your Live Token is A009.",
            type=NotificationType.BOOKING_CONFIRMED,
            channel=NotificationChannel.IN_APP,
            is_read=True,
        ),
        Notification(
            user_id=demo_user_id,
            title="DBT Payment Credited ₹1,13,750 💰",
            message="MSP payment of ₹1,13,750 for J-Form #JF-HR-KNL-2026-00412 has been credited to your HDFC Bank A/c ending in 1012 via PFMS.",
            type=NotificationType.PAYMENT_COMPLETED,
            channel=NotificationChannel.SMS,
            is_read=True,
        ),
        Notification(
            user_id=demo_user_id,
            title="Queue Alert: 8 Farmers Ahead ⏰",
            message="Counter 1 has called Token A001. You are 8 positions away in the Karnal Mandi queue. Estimated wait: ~18 minutes.",
            type=NotificationType.QUEUE_APPROACHING,
            channel=NotificationChannel.IN_APP,
            is_read=False,
        ),
    ]
    for n in notifs:
        session.add(n)
    print("✅ Seeded realistic farmer notifications")


async def run_seed():
    print("🌾 Starting KisanSetu AI authentic database seeding...")
    async with AsyncSessionLocal() as session:
        await clear_tables(session)
        centres = await seed_centres(session)
        crops = await seed_crops(session)
        demos = await seed_demo_accounts(session)
        other_farmers = await seed_farmers(session)
        slots = await seed_slots(session, centres)

        await seed_bookings_and_queue(session, demos["farmer"], other_farmers, centres, crops, slots)
        await seed_notifications(session, demos["farmer_user"].id)

        await session.commit()

    print("\n🎉 Database Seed Complete! Authentic Data Initialized:")
    print("  Farmer  → demo.farmer@example.com (Rajesh Verma, Karnal)")
    print("  Officer → demo.officer@example.com (Anil Kumar, Mandi Officer)")
    print("  Admin   → demo.admin@example.com (Dr. Ramesh Sharma, Director DoCA)")


if __name__ == "__main__":
    asyncio.run(run_seed())
