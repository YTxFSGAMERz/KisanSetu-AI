import { NextResponse } from 'next/server';
import { dbStore, CENTRES } from '@/lib/server-store';

export async function GET(req: Request) {
  const url = new URL(req.url);
  const centreId = Number(url.searchParams.get('centre_id') || 1);
  const centre = CENTRES.find(c => c.id === centreId) || CENTRES[0];

  const tokens = dbStore.queue_tokens.filter(t => t.centre_id === centreId);
  const waitingTokens = tokens.filter(t => t.status === 'WAITING');
  const activeToken = tokens.find(t => t.status === 'CALLED' || t.status === 'PROCESSING');
  const completedTokens = tokens.filter(t => t.status === 'COMPLETED');

  const currentlyProcessingCount = activeToken ? 1 : 0;
  const waitingCount = waitingTokens.length;
  const estWaitMins = Math.round(waitingCount * centre.avg_processing_minutes);

  let congestionLevel: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH' = 'LOW';
  if (waitingCount > 15) congestionLevel = 'VERY_HIGH';
  else if (waitingCount > 8) congestionLevel = 'HIGH';
  else if (waitingCount > 3) congestionLevel = 'MODERATE';

  return NextResponse.json({
    centre_id: centre.id,
    centre_name: centre.name,
    total_in_queue: tokens.length,
    waiting_count: waitingCount,
    processing_count: currentlyProcessingCount,
    completed_today: completedTokens.length,
    currently_serving_token: activeToken?.token_number || 'A001',
    estimated_wait_time_minutes: estWaitMins,
    congestion_level: congestionLevel,
    tokens,
  });
}
