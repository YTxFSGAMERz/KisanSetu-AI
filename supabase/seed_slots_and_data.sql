-- ============================================================
-- Generate 14-day procurement slots for all APMC Mandis in Supabase
-- ============================================================

DO $$
DECLARE
    r_centre RECORD;
    d_offset INT;
    slot_d DATE;
    t_start TIME;
    t_end TIME;
    today_d DATE := CURRENT_DATE;
BEGIN
    FOR r_centre IN SELECT id FROM procurement_centres WHERE is_active = true LOOP
        FOR d_offset IN 0..13 LOOP
            slot_d := today_d + d_offset;
            
            -- Slot 1: 09:00 - 11:00
            INSERT INTO slots (centre_id, slot_date, start_time, end_time, capacity, booked_count, status)
            VALUES (r_centre.id, slot_d, '09:00:00', '11:00:00', 25, 0, 'OPEN')
            ON CONFLICT (centre_id, slot_date, start_time) DO NOTHING;

            -- Slot 2: 11:00 - 13:00
            INSERT INTO slots (centre_id, slot_date, start_time, end_time, capacity, booked_count, status)
            VALUES (r_centre.id, slot_d, '11:00:00', '13:00:00', 25, 0, 'OPEN')
            ON CONFLICT (centre_id, slot_date, start_time) DO NOTHING;

            -- Slot 3: 13:00 - 15:00
            INSERT INTO slots (centre_id, slot_date, start_time, end_time, capacity, booked_count, status)
            VALUES (r_centre.id, slot_d, '13:00:00', '15:00:00', 25, 0, 'OPEN')
            ON CONFLICT (centre_id, slot_date, start_time) DO NOTHING;

            -- Slot 4: 15:00 - 17:00
            INSERT INTO slots (centre_id, slot_date, start_time, end_time, capacity, booked_count, status)
            VALUES (r_centre.id, slot_d, '15:00:00', '17:00:00', 25, 0, 'OPEN')
            ON CONFLICT (centre_id, slot_date, start_time) DO NOTHING;

            -- Slot 5: 17:00 - 19:00
            INSERT INTO slots (centre_id, slot_date, start_time, end_time, capacity, booked_count, status)
            VALUES (r_centre.id, slot_d, '17:00:00', '19:00:00', 25, 0, 'OPEN')
            ON CONFLICT (centre_id, slot_date, start_time) DO NOTHING;
        END LOOP;
    END LOOP;
END $$;
