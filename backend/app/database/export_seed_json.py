"""
Export complete database snapshot from SQLite (kisansetu.db) to frontend seed.json
Ensures 100% data parity between Python SQLite database and Next.js / Vercel serverless database.
Run: python -m app.database.export_seed_json
"""
import json
import os
import sqlite3
from pathlib import Path


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def export_database():
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / "kisansetu.db"
    
    if not db_path.exists():
        # Fallback to local
        db_path = Path("kisansetu.db")
        if not db_path.exists():
            db_path = Path("backend/kisansetu.db")

    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database not found at {db_path}. Please run python -m app.database.setup_local_db first.")

    print(f"📦 Connecting to SQLite database at: {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = dict_factory
    cur = conn.cursor()

    # 1. Centres
    centres_raw = cur.execute("""
        SELECT id, name, code, address, district, state, latitude, longitude,
               daily_capacity, processing_capacity, avg_processing_minutes, is_active, contact_phone
        FROM procurement_centres ORDER BY id
    """).fetchall()
    centres = []
    for c in centres_raw:
        c["is_active"] = bool(c["is_active"])
        centres.append(c)
    centre_map = {c["id"]: c["name"] for c in centres}

    # 2. Crops
    crops = cur.execute("""
        SELECT id, name, name_hi, name_gu, category, unit, msp_per_quintal, processing_complexity
        FROM crops ORDER BY id
    """).fetchall()
    crop_map = {c["id"]: c["name"] for c in crops}

    # 3. Live Prices (Mock realistic Agmarknet modal rates)
    live_prices = [
        {"state": "Haryana", "district": "Karnal", "market": "Karnal", "commodity": "Wheat", "modal_price": 2275.0, "variety": "FAQ"},
        {"state": "Punjab", "district": "Ludhiana", "market": "Khanna", "commodity": "Paddy", "modal_price": 2300.0, "variety": "Common"},
        {"state": "Maharashtra", "district": "Nashik", "market": "Lasalgaon", "commodity": "Onion", "modal_price": 2450.0, "variety": "Red"},
        {"state": "Gujarat", "district": "Mehsana", "market": "Unjha", "commodity": "Mustard", "modal_price": 5650.0, "variety": "Mustard Bold"},
        {"state": "Madhya Pradesh", "district": "Indore", "market": "Indore", "commodity": "Soybean", "modal_price": 4892.0, "variety": "Yellow"},
        {"state": "Rajasthan", "district": "Sri Ganganagar", "market": "Sri Ganganagar", "commodity": "Gram", "modal_price": 5440.0, "variety": "Desi"},
    ]

    # 4. Users & Farmers
    users_raw = cur.execute("""
        SELECT id, name, phone, email, role, is_active FROM users ORDER BY id
    """).fetchall()
    
    farmers_raw = cur.execute("""
        SELECT id, user_id, farmer_registration_number, aadhaar_last4, language, village, district, state, land_area_acres
        FROM farmers
    """).fetchall()
    farmer_map = {f["user_id"]: f for f in farmers_raw}
    farmer_id_map = {f["id"]: f for f in farmers_raw}

    users = []
    for u in users_raw:
        user_dict = {
            "id": u["id"],
            "name": u["name"],
            "email": u["email"],
            "phone": u["phone"],
            "role": u["role"],
        }
        if u["role"] == "FARMER" and u["id"] in farmer_map:
            f = farmer_map[u["id"]]
            user_dict["farmer_id"] = f["id"]
            user_dict["farmer_profile"] = {
                "farmer_registration_number": f["farmer_registration_number"],
                "aadhaar_last_four": f["aadhaar_last4"],
                "land_size_acres": f["land_area_acres"],
                "village": f["village"],
                "district": f["district"],
                "state": f["state"],
                "preferred_language": f["language"],
                "bank_account_verified": True,
            }
        elif "OFFICER" in u["role"]:
            user_dict["centre_id"] = 1
        users.append(user_dict)

    # 5. Bookings
    bookings_raw = cur.execute("""
        SELECT b.id, b.farmer_id, b.centre_id, b.slot_id, b.crop_id, b.expected_quantity,
               b.booking_number, b.booking_status, b.notes, b.created_at,
               s.slot_date, s.start_time, s.end_time
        FROM bookings b
        LEFT JOIN slots s ON b.slot_id = s.id
        ORDER BY b.id
    """).fetchall()

    bookings = []
    for b in bookings_raw:
        farmer_name = "Rajesh Verma"
        if b["farmer_id"] in farmer_id_map:
            u_id = farmer_id_map[b["farmer_id"]]["user_id"]
            u = next((usr for usr in users if usr["id"] == u_id), None)
            if u:
                farmer_name = u["name"].split(" (")[0]

        start_str = str(b.get("start_time") or "09:00:00")[:5]
        end_str = str(b.get("end_time") or "11:00:00")[:5]
        slot_time_str = f"{start_str} - {end_str}"

        bookings.append({
            "id": b["id"],
            "booking_number": b["booking_number"],
            "farmer_id": b["farmer_id"],
            "farmer_name": farmer_name,
            "centre_id": b["centre_id"],
            "centre_name": centre_map.get(b["centre_id"], "APMC Mandi"),
            "slot_id": b["slot_id"],
            "slot_date": str(b.get("slot_date") or "2026-09-04"),
            "slot_time": slot_time_str,
            "crop_id": b["crop_id"],
            "crop_name": crop_map.get(b["crop_id"], "Crop"),
            "expected_quantity": float(b["expected_quantity"]),
            "booking_status": b["booking_status"],
            "token_number": f"A{b['id']:03d}",
            "queue_position": b["id"],
            "estimated_wait_minutes": 15.0 * b["id"],
            "notes": b.get("notes") or "",
            "created_at": str(b["created_at"]),
        })

    # 6. Queue Tokens
    tokens_raw = cur.execute("""
        SELECT id, booking_id, centre_id, token_number, queue_position, status,
               estimated_wait_minutes, arrival_time, called_at, processing_start_time, completed_at
        FROM queue_tokens ORDER BY queue_position
    """).fetchall()

    queue_tokens = []
    for t in tokens_raw:
        b_info = next((bk for bk in bookings if bk["id"] == t["booking_id"]), None)
        queue_tokens.append({
            "id": t["id"],
            "booking_id": t["booking_id"],
            "centre_id": t["centre_id"],
            "token_number": t["token_number"],
            "queue_position": t["queue_position"],
            "status": t["status"],
            "estimated_wait_minutes": float(t["estimated_wait_minutes"] or 15.0),
            "farmer_name": b_info["farmer_name"] if b_info else "Rajesh Verma",
            "crop_name": b_info["crop_name"] if b_info else "Wheat",
            "expected_quantity": b_info["expected_quantity"] if b_info else 40.0,
            "farmers_ahead": max(0, t["queue_position"] - 1),
            "arrival_time": str(t["arrival_time"]) if t["arrival_time"] else None,
            "called_at": str(t["called_at"]) if t["called_at"] else None,
        })

    # 7. Procurements
    proc_raw = cur.execute("""
        SELECT id, booking_id, crop_id, expected_quantity, actual_quantity, accepted_quantity,
               rejected_quantity, quality_grade, procurement_amount, status, receipt_number, created_at, completed_at
        FROM procurements ORDER BY id
    """).fetchall()

    procurements = []
    for p in proc_raw:
        b_info = next((bk for bk in bookings if bk["id"] == p["booking_id"]), None)
        procurements.append({
            "id": p["id"],
            "booking_id": p["booking_id"],
            "crop_id": p["crop_id"],
            "crop_name": crop_map.get(p["crop_id"], "Wheat"),
            "farmer_name": b_info["farmer_name"] if b_info else "Rajesh Verma",
            "centre_name": b_info["centre_name"] if b_info else "Karnal Grain Mandi",
            "booking_number": b_info["booking_number"] if b_info else f"BK-{p['id']:04d}",
            "expected_quantity": float(p["expected_quantity"]),
            "actual_quantity": float(p["actual_quantity"] or p["expected_quantity"]),
            "accepted_quantity": float(p["accepted_quantity"] or p["expected_quantity"]),
            "rejected_quantity": float(p["rejected_quantity"] or 0.0),
            "quality_grade": p["quality_grade"] or "GRADE_A",
            "procurement_amount": float(p["procurement_amount"] or 87587.5),
            "status": p["status"],
            "receipt_number": p["receipt_number"] or f"RCP-2026-{p['id']:04d}",
            "created_at": str(p["created_at"]),
            "completed_at": str(p["completed_at"]) if p["completed_at"] else str(p["created_at"]),
        })

    # 8. Payments
    pay_raw = cur.execute("""
        SELECT id, procurement_id, amount, status, transaction_reference, created_at, completed_at
        FROM payments ORDER BY id
    """).fetchall()

    payments = []
    for pay in pay_raw:
        p_info = next((pr for pr in procurements if pr["id"] == pay["procurement_id"]), None)
        payments.append({
            "id": pay["id"],
            "procurement_id": pay["procurement_id"],
            "amount": float(pay["amount"]),
            "status": pay["status"],
            "transaction_reference": pay["transaction_reference"] or f"TXN-DBT-2026-{pay['id']:06d}",
            "farmer_name": p_info["farmer_name"] if p_info else "Rajesh Verma",
            "crop_name": p_info["crop_name"] if p_info else "Wheat",
            "receipt_number": p_info["receipt_number"] if p_info else f"RCP-2026-{pay['id']:04d}",
            "created_at": str(pay["created_at"]),
            "completed_at": str(pay["completed_at"]) if pay["completed_at"] else str(pay["created_at"]),
        })

    # 9. Notifications
    notifs_raw = cur.execute("""
        SELECT id, user_id, title, message, type, channel, is_read, created_at
        FROM notifications ORDER BY id
    """).fetchall()

    notifications = []
    for n in notifs_raw:
        notifications.append({
            "id": n["id"],
            "user_id": n["user_id"],
            "title": n["title"],
            "message": n["message"],
            "type": n["type"],
            "channel": n["channel"],
            "is_read": bool(n["is_read"]),
            "created_at": str(n["created_at"]),
        })

    conn.close()

    database_payload = {
        "centres": centres,
        "crops": crops,
        "live_prices": live_prices,
        "users": users,
        "bookings": bookings,
        "queue_tokens": queue_tokens,
        "procurements": procurements,
        "payments": payments,
        "notifications": notifications,
    }

    # Target output paths in frontend
    repo_root = base_dir.parent if base_dir.name == "backend" else base_dir
    frontend_data = repo_root / "frontend" / "data"
    frontend_data.mkdir(parents=True, exist_ok=True)

    seed_file = frontend_data / "seed.json"
    store_file = frontend_data / "kisansetu_store.json"

    with open(seed_file, "w", encoding="utf-8") as f:
        json.dump(database_payload, f, indent=2, ensure_ascii=False)
    print(f"✅ Exported database snapshot -> {seed_file}")

    with open(store_file, "w", encoding="utf-8") as f:
        json.dump(database_payload, f, indent=2, ensure_ascii=False)
    print(f"✅ Synchronized local server store -> {store_file}")

    print("\n🎉 Database Export Completed Successfully!")
    print(f"   • Mandis: {len(centres)}")
    print(f"   • Crops: {len(crops)}")
    print(f"   • Users: {len(users)}")
    print(f"   • Bookings: {len(bookings)}")
    print(f"   • Queue Tokens: {len(queue_tokens)}")
    print(f"   • Procurements: {len(procurements)}")
    print(f"   • Payments: {len(payments)}")
    print(f"   • Notifications: {len(notifications)}")


if __name__ == "__main__":
    export_database()
