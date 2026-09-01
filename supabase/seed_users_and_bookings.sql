-- ============================================================
-- Seed initial users, farmers, bookings, and queue tokens in Supabase
-- ============================================================

-- 1. Insert Demo Users (bcrypt hashed, secure default)
INSERT INTO users (id, name, phone, email, password_hash, role, is_active)
VALUES
(1, 'Demo Farmer (Rajesh Verma)', '9876543210', 'demo.farmer@example.com', '$2b$12$e4J1gZ6M5E0bS5m7QkP3TuK6PjXgV.wK4nQ5vX6yZ8lP2rQ1sT3Ku', 'FARMER', true),
(2, 'Demo Officer (Sunil Kumar)', '9876543211', 'demo.officer@example.com', '$2b$12$e4J1gZ6M5E0bS5m7QkP3TuK6PjXgV.wK4nQ5vX6yZ8lP2rQ1sT3Ku', 'PROCUREMENT_OFFICER', true),
(3, 'Demo Admin (Dr. Meena Swaminathan)', '9876543212', 'demo.admin@example.com', '$2b$12$e4J1gZ6M5E0bS5m7QkP3TuK6PjXgV.wK4nQ5vX6yZ8lP2rQ1sT3Ku', 'GOVERNMENT_ADMIN', true)
ON CONFLICT (phone) DO NOTHING;

-- 2. Insert Farmer Profile
INSERT INTO farmers (id, user_id, farmer_registration_number, aadhaar_last4, language, village, district, state, land_area_acres, bank_account_number, bank_ifsc)
VALUES
(1, 1, 'FRN-HR-2026-0001', '4321', 'hi', 'Kachhwa', 'Karnal', 'Haryana', 6.5, '91234567890123', 'SBIN0001234')
ON CONFLICT (farmer_registration_number) DO NOTHING;

-- 3. Insert Initial Live Bookings
INSERT INTO bookings (id, farmer_id, centre_id, slot_id, crop_id, expected_quantity, booking_number, booking_status)
VALUES
(1, 1, 1, 1, 1, 45.0, 'BK-KNL-2026-0001', 'CONFIRMED'),
(2, 1, 1, 2, 2, 60.0, 'BK-KNL-2026-0002', 'CONFIRMED')
ON CONFLICT (booking_number) DO NOTHING;

-- 4. Insert Initial Queue Tokens
INSERT INTO queue_tokens (id, booking_id, centre_id, token_number, queue_position, status, estimated_wait_minutes, arrival_time)
VALUES
(1, 1, 1, 'A001', 1, 'WAITING', 15.0, NOW()),
(2, 2, 1, 'A002', 2, 'WAITING', 30.0, NOW())
ON CONFLICT (booking_id) DO NOTHING;

-- 5. Insert Sample Notifications
INSERT INTO notifications (user_id, title, message, type, channel, is_read)
VALUES
(1, 'Booking Confirmed ✅', 'Your slot for Wheat at Karnal Grain Mandi has been confirmed. Token: A001', 'BOOKING_CONFIRMED', 'IN_APP', true),
(1, 'Slot Reminder 🔔', 'Your procurement slot at Karnal Grain Mandi starts at 9:00 AM.', 'SLOT_REMINDER', 'SMS', false);
