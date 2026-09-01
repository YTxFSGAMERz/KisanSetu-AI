import { NextResponse } from 'next/server';
import { dbStore, CENTRES } from '@/lib/server-store';

export async function GET() {
  const totalVolume = dbStore.procurements.reduce((sum, p) => sum + p.actual_quantity, 0) + 14850.0;
  const totalPayments = dbStore.payments.reduce((sum, p) => sum + p.amount, 0) + 33812500.0;

  const centreRankings = CENTRES.map((c, i) => ({
    centre_id: c.id,
    centre_name: c.name,
    state: c.state,
    district: c.district,
    waiting_count: 3 + (i * 2),
    congestion_level: i === 0 ? 'LOW' : i === 1 ? 'MODERATE' : 'LOW',
    today_volume_quintals: 1200.0 + (i * 350.0),
    avg_wait_minutes: c.avg_processing_minutes * 1.5,
  }));

  const dailyVolumeTrend = [
    { date: '2026-08-26', volume_quintals: 1240.0, farmers_count: 85 },
    { date: '2026-08-27', volume_quintals: 1890.0, farmers_count: 110 },
    { date: '2026-08-28', volume_quintals: 2150.0, farmers_count: 135 },
    { date: '2026-08-29', volume_quintals: 1980.0, farmers_count: 120 },
    { date: '2026-08-30', volume_quintals: 2450.0, farmers_count: 155 },
    { date: '2026-08-31', volume_quintals: 2780.0, farmers_count: 180 },
    { date: '2026-09-01', volume_quintals: 3120.0, farmers_count: 205 },
  ];

  const cropDistribution = [
    { crop_name: 'Wheat', volume_quintals: 8500.0, percentage: 52.0 },
    { crop_name: 'Paddy (Common)', volume_quintals: 4200.0, percentage: 26.0 },
    { crop_name: 'Mustard', volume_quintals: 1800.0, percentage: 11.0 },
    { crop_name: 'Gram', volume_quintals: 1100.0, percentage: 7.0 },
    { crop_name: 'Soybean', volume_quintals: 650.0, percentage: 4.0 },
  ];

  return NextResponse.json({
    total_centres: CENTRES.length,
    active_centres: CENTRES.filter(c => c.is_active).length,
    total_farmers_registered: 1420,
    today_procurement_volume_quintals: totalVolume,
    today_payments_disbursed_inr: totalPayments,
    today_farmers_served: 48,
    today_active_in_queue: dbStore.queue_tokens.filter(t => t.status === 'WAITING').length,
    avg_waiting_time_minutes: 18.5,
    centre_congestion_rankings: centreRankings,
    daily_volume_trend: dailyVolumeTrend,
    crop_distribution: cropDistribution,
  });
}
