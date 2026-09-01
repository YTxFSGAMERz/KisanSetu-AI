-- ============================================================
-- KisanSetu AI — Supabase Database Migration
-- Problem Statement 26032 | Department of Consumer Affairs (DoCA)
-- ============================================================

-- 1. Custom Enum Types
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('FARMER', 'PROCUREMENT_OFFICER', 'CENTRE_ADMIN', 'GOVERNMENT_ADMIN');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE slot_status AS ENUM ('OPEN', 'FULL', 'CANCELLED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE booking_status AS ENUM ('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED', 'NO_SHOW');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE token_status AS ENUM ('WAITING', 'CALLED', 'PROCESSING', 'COMPLETED', 'SKIPPED', 'NO_SHOW');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE procurement_status AS ENUM ('IN_PROGRESS', 'COMPLETED', 'REJECTED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE quality_grade AS ENUM ('GRADE_A', 'STANDARD', 'BELOW_STANDARD');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE payment_status AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE notification_type AS ENUM ('BOOKING_CONFIRMED', 'SLOT_REMINDER', 'QUEUE_APPROACHING', 'FARMER_CALLED', 'PROCUREMENT_COMPLETED', 'PAYMENT_COMPLETED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE notification_channel AS ENUM ('IN_APP', 'SMS', 'WHATSAPP');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role user_role NOT NULL DEFAULT 'FARMER',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Farmers Table
CREATE TABLE IF NOT EXISTS farmers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    farmer_registration_number VARCHAR(100) UNIQUE NOT NULL,
    aadhaar_last4 VARCHAR(4),
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    village VARCHAR(255),
    district VARCHAR(255),
    state VARCHAR(255),
    land_area_acres FLOAT,
    bank_account_number VARCHAR(50),
    bank_ifsc VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Procurement Centres Table (Real APMC Mandis)
CREATE TABLE IF NOT EXISTS procurement_centres (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    address TEXT NOT NULL,
    district VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    daily_capacity INTEGER NOT NULL DEFAULT 100,
    processing_capacity INTEGER NOT NULL DEFAULT 5,
    avg_processing_minutes FLOAT NOT NULL DEFAULT 20.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    contact_phone VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Crops Table (Real CACP MSP Commodities)
CREATE TABLE IF NOT EXISTS crops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    name_hi VARCHAR(100),
    name_gu VARCHAR(100),
    category VARCHAR(50) NOT NULL,
    unit VARCHAR(20) NOT NULL DEFAULT 'quintal',
    msp_per_quintal FLOAT NOT NULL,
    processing_complexity FLOAT NOT NULL DEFAULT 1.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- 6. Slots Table
CREATE TABLE IF NOT EXISTS slots (
    id SERIAL PRIMARY KEY,
    centre_id INTEGER NOT NULL REFERENCES procurement_centres(id) ON DELETE CASCADE,
    slot_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 20,
    booked_count INTEGER NOT NULL DEFAULT 0,
    status slot_status NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_centre_slot UNIQUE (centre_id, slot_date, start_time)
);

-- 7. Bookings Table
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
    centre_id INTEGER NOT NULL REFERENCES procurement_centres(id) ON DELETE CASCADE,
    slot_id INTEGER NOT NULL REFERENCES slots(id) ON DELETE CASCADE,
    crop_id INTEGER NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    expected_quantity FLOAT NOT NULL,
    booking_number VARCHAR(50) UNIQUE NOT NULL,
    booking_status booking_status NOT NULL DEFAULT 'CONFIRMED',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. Queue Tokens Table
CREATE TABLE IF NOT EXISTS queue_tokens (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER UNIQUE NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    centre_id INTEGER NOT NULL REFERENCES procurement_centres(id) ON DELETE CASCADE,
    token_number VARCHAR(20) NOT NULL,
    queue_position INTEGER NOT NULL,
    status token_status NOT NULL DEFAULT 'WAITING',
    estimated_wait_minutes FLOAT NOT NULL DEFAULT 0.0,
    arrival_time TIMESTAMPTZ,
    called_at TIMESTAMPTZ,
    processing_start_time TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. Procurements Table
CREATE TABLE IF NOT EXISTS procurements (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER UNIQUE NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    crop_id INTEGER NOT NULL REFERENCES crops(id),
    expected_quantity FLOAT NOT NULL,
    actual_quantity FLOAT NOT NULL,
    accepted_quantity FLOAT NOT NULL,
    rejected_quantity FLOAT NOT NULL DEFAULT 0.0,
    quality_grade quality_grade NOT NULL DEFAULT 'GRADE_A',
    procurement_amount FLOAT NOT NULL,
    status procurement_status NOT NULL DEFAULT 'IN_PROGRESS',
    processed_by INTEGER REFERENCES users(id),
    rejection_reason TEXT,
    receipt_number VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 10. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    procurement_id INTEGER UNIQUE NOT NULL REFERENCES procurements(id) ON DELETE CASCADE,
    amount FLOAT NOT NULL,
    status payment_status NOT NULL DEFAULT 'PENDING',
    transaction_reference VARCHAR(100) UNIQUE,
    initiated_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 11. Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type notification_type NOT NULL,
    channel notification_channel NOT NULL DEFAULT 'IN_APP',
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    reference_id INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Query Performance Indexes ───────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_slots_centre_date ON slots(centre_id, slot_date);
CREATE INDEX IF NOT EXISTS idx_bookings_farmer ON bookings(farmer_id);
CREATE INDEX IF NOT EXISTS idx_queue_centre_status ON queue_tokens(centre_id, status);
CREATE INDEX IF NOT EXISTS idx_procurements_booking ON procurements(booking_id);
CREATE INDEX IF NOT EXISTS idx_payments_procurement ON payments(procurement_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);
