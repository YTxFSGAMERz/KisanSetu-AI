import sqlite3
from datetime import datetime, timezone

conn = sqlite3.connect('backend/kisansetu.db')
cur = conn.cursor()

more_farmers = [
    ('A012', 4, 35.0, 12),
    ('A013', 5, 25.0, 13),
    ('A014', 1, 60.0, 14),
    ('A015', 13, 40.0, 15),
    ('A016', 1, 45.0, 16),
    ('A017', 4, 30.0, 17),
    ('A018', 1, 55.0, 18),
    ('A019', 2, 40.0, 19),
    ('A020', 1, 35.0, 20),
    ('A021', 1, 50.0, 11),
]

now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

cur.execute('SELECT MAX(id) FROM bookings')
max_b = cur.fetchone()[0] or 0

cur.execute('SELECT MAX(id) FROM queue_tokens')
max_t = cur.fetchone()[0] or 0

for idx, (tok, crop_id, qty, farmer_id) in enumerate(more_farmers, start=1):
    max_b += 1
    max_t += 1
    b_num = f'BK-KNL-2026-{max_b:04d}'
    cur.execute('''
        INSERT INTO bookings (id, farmer_id, centre_id, slot_id, crop_id, expected_quantity, booking_number, booking_status, notes, created_at, updated_at)
        VALUES (?, ?, 1, 6, ?, ?, ?, 'CONFIRMED', 'Afternoon slot', ?, ?)
    ''', (max_b, farmer_id, crop_id, qty, b_num, now, now))
    
    cur.execute('''
        INSERT INTO queue_tokens (id, booking_id, centre_id, token_number, queue_position, status, estimated_wait_minutes, arrival_time, created_at)
        VALUES (?, ?, 1, ?, ?, 'WAITING', ?, ?, ?)
    ''', (max_t, max_b, tok, idx, idx * 15.0, now, now))

conn.commit()
cur.execute("SELECT COUNT(*) FROM queue_tokens WHERE centre_id=1 AND status='WAITING'")
print("SQLite waiting tokens for centre 1:", cur.fetchone()[0])
conn.close()
