-- ============================================================
-- Migration: Enable Row Level Security (RLS) on all public tables
-- Optimized with (SELECT auth.uid()) for InitPlan caching
-- ============================================================

-- 1. Enable RLS on all public tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.farmers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.procurement_centres ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crops ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.queue_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.procurements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- 2. Drop any prior policies to allow clean recreation
DROP POLICY IF EXISTS "Allow public read-only access for centres" ON public.procurement_centres;
DROP POLICY IF EXISTS "Allow public read-only access for crops" ON public.crops;
DROP POLICY IF EXISTS "Allow public read-only access for slots" ON public.slots;
DROP POLICY IF EXISTS "Users can view their own profile" ON public.users;
DROP POLICY IF EXISTS "Farmers can view their own record" ON public.farmers;
DROP POLICY IF EXISTS "Farmers can view their own bookings" ON public.bookings;
DROP POLICY IF EXISTS "Farmers can view their own queue tokens" ON public.queue_tokens;
DROP POLICY IF EXISTS "Farmers can view their own procurements" ON public.procurements;
DROP POLICY IF EXISTS "Farmers can view their own payments" ON public.payments;
DROP POLICY IF EXISTS "Users can view own notifications" ON public.notifications;
DROP POLICY IF EXISTS "Users can update own notifications" ON public.notifications;

-- 3. Public Read Policies for Reference Data (Centres, Crops, Slots)
CREATE POLICY "Allow public read-only access for centres"
    ON public.procurement_centres FOR SELECT
    USING (is_active = true);

CREATE POLICY "Allow public read-only access for crops"
    ON public.crops FOR SELECT
    USING (is_active = true);

CREATE POLICY "Allow public read-only access for slots"
    ON public.slots FOR SELECT
    USING (status = 'OPEN');

-- 4. User-Specific Policies (Optimized with (SELECT auth.uid()))
CREATE POLICY "Users can view their own profile"
    ON public.users FOR SELECT
    USING (id::text = (SELECT auth.uid()::text) OR (SELECT auth.role()) = 'service_role');

CREATE POLICY "Farmers can view their own record"
    ON public.farmers FOR SELECT
    USING (user_id::text = (SELECT auth.uid()::text) OR (SELECT auth.role()) = 'service_role');

CREATE POLICY "Farmers can view their own bookings"
    ON public.bookings FOR SELECT
    USING (
        farmer_id IN (SELECT id FROM public.farmers WHERE user_id::text = (SELECT auth.uid()::text))
        OR (SELECT auth.role()) = 'service_role'
    );

CREATE POLICY "Farmers can view their own queue tokens"
    ON public.queue_tokens FOR SELECT
    USING (
        booking_id IN (
            SELECT b.id FROM public.bookings b
            JOIN public.farmers f ON f.id = b.farmer_id
            WHERE f.user_id::text = (SELECT auth.uid()::text)
        )
        OR (SELECT auth.role()) = 'service_role'
    );

CREATE POLICY "Farmers can view their own procurements"
    ON public.procurements FOR SELECT
    USING (
        booking_id IN (
            SELECT b.id FROM public.bookings b
            JOIN public.farmers f ON f.id = b.farmer_id
            WHERE f.user_id::text = (SELECT auth.uid()::text)
        )
        OR (SELECT auth.role()) = 'service_role'
    );

CREATE POLICY "Farmers can view their own payments"
    ON public.payments FOR SELECT
    USING (
        procurement_id IN (
            SELECT p.id FROM public.procurements p
            JOIN public.bookings b ON b.id = p.booking_id
            JOIN public.farmers f ON f.id = b.farmer_id
            WHERE f.user_id::text = (SELECT auth.uid()::text)
        )
        OR (SELECT auth.role()) = 'service_role'
    );

CREATE POLICY "Users can view own notifications"
    ON public.notifications FOR SELECT
    USING (user_id::text = (SELECT auth.uid()::text) OR (SELECT auth.role()) = 'service_role');

CREATE POLICY "Users can update own notifications"
    ON public.notifications FOR UPDATE
    USING (user_id::text = (SELECT auth.uid()::text) OR (SELECT auth.role()) = 'service_role');
