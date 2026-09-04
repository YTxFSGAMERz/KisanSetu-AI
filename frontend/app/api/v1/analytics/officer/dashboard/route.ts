import { NextResponse } from 'next/server';
import { dbStore, CENTRES } from '@/lib/server-store';

export async function GET(req: Request) {
  const url = new URL(req.url);
  const centreId = Number(url.searchParams.get('centre_id') || '1');
  const centre = CENTRES.find(c => c.id === centreId) || CENTRES[0];

  return NextResponse.json({
    centre_id: centre.id,
    centre_name: centre.name,
    capacity_utilization_pct: 68.5,
    current_queue_length: dbStore.queue_tokens.filter(t => t.status === 'WAITING').length,
    farmers_served_today: 14,
    avg_processing_minutes: centre.avg_processing_minutes,
    today_procurement_volume_quintals: 540.0,
    active_tokens: dbStore.queue_tokens,
  });
}
