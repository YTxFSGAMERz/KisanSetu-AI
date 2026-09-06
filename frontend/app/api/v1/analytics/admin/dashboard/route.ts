import { NextResponse } from 'next/server';
import { dbStore, CENTRES, CROPS } from '@/lib/server-store';
import { db } from '@/lib/db';

/**
 * Admin Dashboard Analytics — 100% Dynamic Real Data
 * All KPI values are computed live from active database records.
 * No hardcoded offsets, mock constants, or static charts.
 */
export async function GET() {
  const state = db.getState();

  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD

  // ── Centres ──────────────────────────────────────────────────────────────────
  const activeCentres = CENTRES.filter((c) => c.is_active);
  const total_active_centres = activeCentres.length;

  // ── Registered Farmers ───────────────────────────────────────────────────────
  const total_registered_farmers = state.users.filter(
    (u: any) => u.role === 'FARMER'
  ).length;

  // ── Farmers served today (queue tokens COMPLETED on today's date) ────────────
  const servedToday = dbStore.queue_tokens.filter((t) => {
    if (t.status !== 'COMPLETED') return false;
    if (!t.completed_at) return false;
    return t.completed_at.startsWith(today);
  });
  const farmers_served_today = servedToday.length;

  // ── Average waiting time (from all COMPLETED tokens that have timing data) ───
  const completedWithTimes = dbStore.queue_tokens.filter(
    (t) => t.status === 'COMPLETED' && typeof t.estimated_wait_minutes === 'number'
  );
  const avg_waiting_minutes =
    completedWithTimes.length > 0
      ? Math.round(
          (completedWithTimes.reduce((sum, t) => sum + (t.estimated_wait_minutes || 0), 0) /
            completedWithTimes.length) *
            10
        ) / 10
      : 0;

  // ── Total procurement quintals (real sum — no offsets) ───────────────────────
  const completedProcurements = dbStore.procurements.filter(
    (p) => p.status === 'COMPLETED'
  );
  const total_procurement_quintals = parseFloat(
    completedProcurements
      .reduce((sum, p) => sum + (p.accepted_quantity || 0), 0)
      .toFixed(2)
  );

  // ── Payment completion rate ──────────────────────────────────────────────────
  const totalPayments = dbStore.payments.length;
  const completedPayments = dbStore.payments.filter((p) => p.status === 'COMPLETED').length;
  const payment_completion_rate =
    totalPayments > 0
      ? Math.round((completedPayments / totalPayments) * 1000) / 10
      : 0;

  // ── No-show count today ──────────────────────────────────────────────────────
  const noShowsToday = dbStore.queue_tokens.filter((t) => {
    if (t.status !== 'NO_SHOW') return false;
    // No-show tokens don't have completed_at — use the booking date via centre
    // For now we use the most recent available date stamp
    const stamp = t.completed_at || t.called_at || '';
    return stamp.startsWith(today);
  }).length;

  // ── No-show rate ─────────────────────────────────────────────────────────────
  const no_show_rate =
    farmers_served_today + noShowsToday > 0
      ? Math.round((noShowsToday / (farmers_served_today + noShowsToday)) * 1000) / 10
      : 0;

  // ── Per-centre analytics ──────────────────────────────────────────────────────
  const centreMap = new Map(CENTRES.map((c) => [c.id, c]));
  const cropMsp = new Map(CROPS.map((c) => [c.id, c.msp_per_quintal]));

  const centres = activeCentres.map((centre) => {
    const centreTokens = dbStore.queue_tokens.filter((t) => t.centre_id === centre.id);

    const completedTodayTokens = centreTokens.filter(
      (t) => t.status === 'COMPLETED' && t.completed_at?.startsWith(today)
    );
    const noShowTodayTokens = centreTokens.filter(
      (t) =>
        t.status === 'NO_SHOW' &&
        (t.completed_at || t.called_at || '').startsWith(today)
    );
    const waitingTokens = centreTokens.filter((t) => t.status === 'WAITING');

    const completed_today = completedTodayTokens.length;
    const no_shows_today = noShowTodayTokens.length;

    // Congestion score: (waiting / daily_capacity) * 100, clamped to 0–100
    const congestion_score = Math.min(
      100,
      Math.round((waitingTokens.length / Math.max(centre.daily_capacity, 1)) * 100)
    );

    // Real procurements for this centre (via booking → centre mapping)
    const centreBookingIds = new Set(
      dbStore.bookings
        .filter((b) => b.centre_id === centre.id)
        .map((b) => b.id)
    );
    const centreProcurements = dbStore.procurements.filter(
      (p) => p.status === 'COMPLETED' && centreBookingIds.has(p.booking_id)
    );
    const total_quantity_kg = parseFloat(
      centreProcurements.reduce((sum, p) => sum + (p.accepted_quantity || 0), 0).toFixed(2)
    );

    // Real payments disbursed for this centre
    const centreProcIds = new Set(centreProcurements.map((p) => p.id));
    const total_amount = parseFloat(
      dbStore.payments
        .filter((pay) => pay.status === 'COMPLETED' && centreProcIds.has(pay.procurement_id))
        .reduce((sum, pay) => sum + (pay.amount || 0), 0)
        .toFixed(2)
    );

    // Avg processing time from completed tokens with timing info
    const avgProcessingTokens = completedTodayTokens.filter(
      (t) => typeof t.estimated_wait_minutes === 'number'
    );
    const avg_processing_minutes =
      avgProcessingTokens.length > 0
        ? Math.round(
            (avgProcessingTokens.reduce(
              (sum, t) => sum + (t.estimated_wait_minutes || 0),
              0
            ) /
              avgProcessingTokens.length) *
              10
          ) / 10
        : centre.avg_processing_minutes;

    return {
      centre_id: centre.id,
      centre_name: centre.name,
      congestion_score,
      farmers_today: completed_today,
      completed_today,
      no_shows_today,
      avg_processing_minutes,
      total_quantity_kg,
      total_amount,
    };
  });

  // ── 7-Day daily volume chart (rolling, dynamic) ───────────────────────────────
  const daily_volume_chart: { date: string; quantity: number; count: number }[] = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().split('T')[0];

    const dayProcs = dbStore.procurements.filter(
      (p) =>
        p.status === 'COMPLETED' &&
        (p.completed_at || p.created_at)?.startsWith(dateStr)
    );
    daily_volume_chart.push({
      date: dateStr,
      quantity: parseFloat(
        dayProcs.reduce((sum, p) => sum + (p.accepted_quantity || 0), 0).toFixed(2)
      ),
      count: dayProcs.length,
    });
  }

  return NextResponse.json({
    total_active_centres,
    total_registered_farmers,
    farmers_served_today,
    avg_waiting_minutes,
    total_procurement_quintals,
    payment_completion_rate,
    centres,
    daily_volume_chart,
    no_show_rate,
  });
}
