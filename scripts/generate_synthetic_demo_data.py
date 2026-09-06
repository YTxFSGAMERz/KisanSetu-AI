"""
KisanSetu AI — Synthetic Demo Data Generator
==============================================
Generates realistic, fully fictional demo data for KisanSetu.

Uses:
  - Real crop names and MSP values (from processed MSP reference)
  - Real districts and states (from location reference)
  - Real mandi names (from eNAM reference)
  - Fictional farmer names, registration numbers, booking numbers
  - No real Aadhaar, bank details, or phone numbers

ALL generated data is clearly marked: SYNTHETIC_DEMO_DATA

Output:
  data/processed/synthetic/centres.json
  data/processed/synthetic/crops.json
  data/processed/synthetic/farmers.json
  data/processed/synthetic/bookings.json
  data/processed/synthetic/queue_events.json

Usage:
  python scripts/generate_synthetic_demo_data.py
  python scripts/generate_synthetic_demo_data.py --seed 42
  python scripts/generate_synthetic_demo_data.py --dry-run
"""
import argparse
import csv
import json
import random
import string
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
OUTPUT_DIR = PROCESSED_DIR / "synthetic"
MSP_REF = PROCESSED_DIR / "msp" / "msp_reference.csv"
LOCATION_REF = PROCESSED_DIR / "centres" / "location_reference.csv"
ENAM_REF = PROCESSED_DIR / "centres" / "enam_mandi_reference.csv"

# ─── Synthetic name pools (no real persons) ──────────────────────────────────
# These are generic, non-identifying first/last name pools for demo purposes.
FIRST_NAMES = [
    "Ramesh", "Suresh", "Mahesh", "Dinesh", "Ganesh", "Rajesh", "Naresh",
    "Pradeep", "Sandeep", "Hardeep", "Mandeep", "Kuldeep", "Baldeep",
    "Arvind", "Pramod", "Vinod", "Manoj", "Sanjay", "Vijay", "Ajay",
    "Harish", "Girish", "Manish", "Bharat", "Prakash", "Aakash", "Subhash",
    "Ravi", "Kavi", "Savi", "Devi", "Laxmi", "Kamla", "Shanta",
    "Gurpreet", "Harpreet", "Manpreet", "Jaspreet", "Amanpreet",
    "Kiran", "Seema", "Reema", "Geeta", "Meera", "Heera",
]
LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Kumar", "Singh", "Yadav", "Patel",
    "Joshi", "Chauhan", "Rawat", "Negi", "Bisht", "Thakur",
    "Reddy", "Naidu", "Raju", "Rao", "Murthy", "Chary",
    "Patil", "More", "Jadhav", "Desai", "Mehta", "Shah",
    "Chaudhary", "Mandal", "Sahu", "Nayak", "Behera",
    "Gill", "Dhillon", "Sidhu", "Grewal", "Sandhu", "Brar",
]

# Crop processing complexity relative to Wheat=1.0
CROP_COMPLEXITY = {
    "Wheat": 1.0, "Paddy": 1.1, "Maize": 0.9, "Bajra": 0.9,
    "Jowar": 0.95, "Gram": 1.1, "Tur": 1.2, "Moong": 1.2,
    "Urad": 1.2, "Mustard": 1.0, "Soyabean": 1.0, "Groundnut": 1.3,
    "Cotton": 1.5, "Barley": 0.9,
}


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_msp_reference() -> dict[str, float]:
    """Load MSP as {crop: msp} for 2025-26 season (most current)."""
    rows = load_csv(MSP_REF)
    msp_map = {}
    for r in rows:
        if r.get("marketing_season") == "2025-26":
            crop = r.get("commodity", r.get("crop", "")).strip().title()
            try:
                msp_map[crop] = float(r["msp"])
            except (ValueError, KeyError):
                pass
    # Fallback embedded values if file not yet processed
    if not msp_map:
        msp_map = {
            "Wheat": 2425.0, "Paddy": 2369.0, "Maize": 2340.0,
            "Mustard": 5950.0, "Gram": 5650.0, "Tur": 8000.0,
            "Moong": 9100.0, "Urad": 7800.0, "Groundnut": 7100.0,
            "Soyabean": 5330.0, "Cotton": 7521.0, "Barley": 1980.0,
            "Bajra": 2735.0, "Jowar": 3590.0,
        }
    return msp_map


def load_locations() -> list[dict]:
    locations = load_csv(LOCATION_REF)
    if not locations:
        # Minimal fallback
        return [
            {"state": "Punjab", "district": "Ludhiana", "pincode": "141001"},
            {"state": "Haryana", "district": "Karnal", "pincode": "132001"},
            {"state": "Madhya Pradesh", "district": "Indore", "pincode": "452001"},
            {"state": "Uttar Pradesh", "district": "Lucknow", "pincode": "226001"},
            {"state": "Rajasthan", "district": "Jaipur", "pincode": "302001"},
        ]
    return locations


def generate_centres(enam_rows: list[dict], locations: list[dict], rng: random.Random) -> list[dict]:
    """Generate synthetic procurement centre records from eNAM reference data."""
    centres = []
    used_codes = set()

    source_rows = enam_rows if enam_rows else [
        {"centre_name": "Khanna Mandi", "state": "Punjab", "district": "Ludhiana"},
        {"centre_name": "Karnal Mandi", "state": "Haryana", "district": "Karnal"},
        {"centre_name": "Indore Mandi", "state": "Madhya Pradesh", "district": "Indore"},
        {"centre_name": "Sri Ganganagar", "state": "Rajasthan", "district": "Sri Ganganagar"},
        {"centre_name": "Nizamabad", "state": "Telangana", "district": "Nizamabad"},
    ]

    for i, row in enumerate(source_rows[:15]):  # Max 15 demo centres
        state = row.get("state", "")
        district = row.get("district", "")
        name = row.get("centre_name", f"Mandi {i+1}")

        # Generate unique code
        code_base = f"PC{state[:2].upper()}{district[:3].upper()}"
        code = code_base
        suffix = 1
        while code in used_codes:
            code = f"{code_base}{suffix:02d}"
            suffix += 1
        used_codes.add(code)

        # Find a matching location for address
        loc = next((l for l in locations if l.get("district", "").lower() == district.lower()), None)
        pincode = loc.get("pincode", "000000") if loc else "000000"

        centres.append({
            "_synthetic": True,
            "_data_type": "SYNTHETIC_DEMO_DATA",
            "code": code,
            "name": f"{name} Procurement Centre",
            "address": f"Near {name}, {district}, {state} - {pincode}",
            "district": district,
            "state": state,
            "latitude": None,
            "longitude": None,
            "daily_capacity": rng.choice([80, 100, 120, 150]),
            "processing_capacity": rng.choice([4, 5, 6, 8]),
            "avg_processing_minutes": rng.choice([15.0, 18.0, 20.0, 22.0, 25.0]),
            "is_active": True,
            "contact_phone": None,
        })

    return centres


def generate_crops(msp_map: dict) -> list[dict]:
    """Generate crop seed data using real MSP values."""
    crops = []
    hindi_names = {
        "Wheat": "गेहूं", "Paddy": "धान", "Maize": "मक्का", "Mustard": "सरसों",
        "Gram": "चना", "Tur": "अरहर", "Moong": "मूंग", "Urad": "उड़द",
        "Groundnut": "मूंगफली", "Soyabean": "सोयाबीन", "Cotton": "कपास",
        "Barley": "जौ", "Bajra": "बाजरा", "Jowar": "ज्वार",
    }
    categories = {
        "Wheat": "cereal", "Paddy": "cereal", "Maize": "cereal",
        "Bajra": "cereal", "Jowar": "cereal", "Barley": "cereal",
        "Gram": "pulse", "Tur": "pulse", "Moong": "pulse", "Urad": "pulse",
        "Mustard": "oilseed", "Soyabean": "oilseed", "Groundnut": "oilseed",
        "Cotton": "fibre",
    }

    for crop_name, msp in msp_map.items():
        crops.append({
            "_synthetic": False,  # MSP values are REAL
            "_msp_source": "CACP Official (embedded reference)",
            "name": crop_name,
            "name_hi": hindi_names.get(crop_name, ""),
            "name_gu": "",
            "category": categories.get(crop_name, "other"),
            "unit": "quintal",
            "msp_per_quintal": msp,
            "processing_complexity": CROP_COMPLEXITY.get(crop_name, 1.0),
        })

    return crops


def generate_farmers(locations: list[dict], n: int, rng: random.Random) -> list[dict]:
    """Generate fictional farmer profiles. NO real PII."""
    farmers = []
    used_regs = set()

    for i in range(n):
        loc = rng.choice(locations)
        state = loc.get("state", "Unknown")
        district = loc.get("district", "Unknown")

        # Fictional registration number — not based on any real registry
        reg = f"KS{state[:2].upper()}{rng.randint(100000, 999999)}"
        while reg in used_regs:
            reg = f"KS{state[:2].upper()}{rng.randint(100000, 999999)}"
        used_regs.add(reg)

        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"

        farmers.append({
            "_synthetic": True,
            "_data_type": "SYNTHETIC_DEMO_DATA",
            "id": i + 1,
            "name": name,
            "farmer_registration_number": reg,
            "aadhaar_last4": None,          # Never generated
            "language": rng.choice(["en", "hi", "hi", "en"]),
            "village": f"Village {rng.randint(1, 500)}",
            "district": district,
            "state": state,
            "land_area_acres": round(rng.uniform(0.5, 15.0), 1),
        })

    return farmers


def generate_bookings(
    farmers: list[dict],
    centres: list[dict],
    crops: list[dict],
    start_date: date,
    days: int,
    rng: random.Random,
) -> list[dict]:
    """Generate fictional booking records."""
    bookings = []
    used_booking_nums = set()

    kharif_crops = ["Paddy", "Maize", "Bajra", "Jowar", "Tur", "Moong", "Groundnut", "Soyabean", "Cotton"]
    rabi_crops = ["Wheat", "Mustard", "Gram", "Masur", "Barley", "Safflower"]
    month = start_date.month
    season_crops = kharif_crops if month in [10, 11, 12, 1, 2] else rabi_crops

    available_crops = [c for c in crops if c["name"] in season_crops] or crops

    slot_times = [
        (time(9, 0), time(10, 0)),
        (time(10, 0), time(11, 0)),
        (time(11, 0), time(12, 0)),
        (time(14, 0), time(15, 0)),
        (time(15, 0), time(16, 0)),
    ]

    statuses = ["CONFIRMED"] * 7 + ["COMPLETED"] * 2 + ["CANCELLED"] * 1

    for b_id in range(1, len(farmers) * 2):
        farmer = rng.choice(farmers)
        centre = rng.choice(centres)
        crop = rng.choice(available_crops)

        booking_date = start_date + timedelta(days=rng.randint(0, days - 1))
        slot_start, slot_end = rng.choice(slot_times)

        bn = f"BK{booking_date.strftime('%y%m%d')}{rng.randint(1000, 9999)}"
        while bn in used_booking_nums:
            bn = f"BK{booking_date.strftime('%y%m%d')}{rng.randint(1000, 9999)}"
        used_booking_nums.add(bn)

        quantity = round(rng.uniform(1.0, 50.0), 1)

        bookings.append({
            "_synthetic": True,
            "_data_type": "SYNTHETIC_DEMO_DATA",
            "id": b_id,
            "booking_number": bn,
            "farmer_id": farmer["id"],
            "centre_code": centre["code"],
            "crop_name": crop["name"],
            "booking_date": str(booking_date),
            "slot_start": str(slot_start),
            "slot_end": str(slot_end),
            "expected_quantity_quintals": quantity,
            "expected_payment_inr": round(quantity * crop.get("msp_per_quintal", 0), 2),
            "booking_status": rng.choice(statuses),
        })

    return bookings


def generate_queue_events(bookings: list[dict], rng: random.Random) -> list[dict]:
    """Generate queue event timelines for completed bookings."""
    events = []
    completed = [b for b in bookings if b["booking_status"] == "COMPLETED"]

    for b in completed:
        slot_hour = int(b["slot_start"].split(":")[0])
        base_dt = datetime(2026, 9, 1, slot_hour, 0, tzinfo=timezone.utc)

        arrival_offset = rng.randint(-10, 30)  # Can arrive early or late
        arrival = base_dt + timedelta(minutes=arrival_offset)
        call_lag = rng.randint(5, 45)
        processing_start = arrival + timedelta(minutes=call_lag)
        processing_duration = rng.randint(10, 40)
        completed_at = processing_start + timedelta(minutes=processing_duration)

        events.append({
            "_synthetic": True,
            "_data_type": "SYNTHETIC_DEMO_DATA",
            "booking_number": b["booking_number"],
            "token_number": f"A{rng.randint(1, 200):03d}",
            "queue_position": rng.randint(1, 80),
            "arrival_time": arrival.isoformat(),
            "called_at": (arrival + timedelta(minutes=call_lag - 2)).isoformat(),
            "processing_start_time": processing_start.isoformat(),
            "completed_at": completed_at.isoformat(),
            "actual_wait_minutes": round(call_lag, 1),
            "processing_minutes": processing_duration,
            "status": "COMPLETED",
        })

    return events


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic KisanSetu demo data")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--farmers", type=int, default=200, help="Number of synthetic farmers")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without writing files")
    parser.add_argument("--days", type=int, default=30, help="Days of booking history to generate")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[synthetic] Seed: {args.seed}")
    print(f"[synthetic] ALL generated data is SYNTHETIC_DEMO_DATA — no real PII")

    # Load reference data
    msp_map = load_msp_reference()
    locations = load_locations()
    enam_rows = load_csv(ENAM_REF)

    print(f"[synthetic] MSP crops loaded: {len(msp_map)}")
    print(f"[synthetic] Locations loaded: {len(locations)}")
    print(f"[synthetic] eNAM mandis loaded: {len(enam_rows)}")

    # Generate datasets
    centres = generate_centres(enam_rows, locations, rng)
    crops = generate_crops(msp_map)
    farmers = generate_farmers(locations, args.farmers, rng)
    start_date = date(2026, 3, 1)  # Rabi season
    bookings = generate_bookings(farmers, centres, crops, start_date, args.days, rng)
    queue_events = generate_queue_events(bookings, rng)

    print(f"\n[synthetic] Generated:")
    print(f"  Centres:      {len(centres)}")
    print(f"  Crops:        {len(crops)} (with real MSP values)")
    print(f"  Farmers:      {len(farmers)} (all fictional)")
    print(f"  Bookings:     {len(bookings)}")
    print(f"  Queue events: {len(queue_events)}")

    if args.dry_run:
        print("\n[synthetic] --dry-run: Files NOT written.")
        return

    outputs = {
        "centres.json": centres,
        "crops.json": crops,
        "farmers.json": farmers,
        "bookings.json": bookings,
        "queue_events.json": queue_events,
    }

    for filename, data in outputs.items():
        out = OUTPUT_DIR / filename
        out.write_text(json.dumps({
            "_notice": "SYNTHETIC_DEMO_DATA — Generated by KisanSetu AI data pipeline",
            "_seed": args.seed,
            "_generated_at": datetime.now(timezone.utc).isoformat(),
            "count": len(data),
            "records": data,
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[synthetic] Written: {out} ({len(data)} records)")

    print(f"\n[synthetic] ✅ Done. All data is SYNTHETIC_DEMO_DATA.")


if __name__ == "__main__":
    main()
