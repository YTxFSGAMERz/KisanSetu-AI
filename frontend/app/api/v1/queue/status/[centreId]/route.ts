import { NextResponse } from 'next/server';
import { dbStore, CENTRES } from '@/lib/server-store';

/**
 * GET /api/v1/queue/status/[centreId]
 * Returns queue status for a specific centre.
 */
export async function GET(
  req: Request,
  { params }: { params: Promise<{ centreId: string }> }
) {
  const { centreId } = await params;
  const cId = Number(centreId) || 1;
  const centre = CENTRES.find(c => c.id === cId) || CENTRES[0];

  const tokens = dbStore.queue_tokens.filter(t => t.centre_id === cId);
  const waitingTokens = tokens.filter(t => t.status === 'WAITING');
  const activeToken = tokens.find(t => t.status === 'PROCESSING') || tokens.find(t => t.status === 'CALLED') || null;
  const processingTokens = tokens.filter(t => t.status === 'PROCESSING' || t.status === 'CALLED');
  const completedTokens = tokens.filter(t => t.status === 'COMPLETED');
  const noShowTokens = tokens.filter(t => t.status === 'NO_SHOW');

  const waitingCount = waitingTokens.length;
  const estWaitMins = Math.round(waitingCount * (centre?.avg_processing_minutes || 20));

  let congestionLevel: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH' = 'LOW';
  if (waitingCount > 15) congestionLevel = 'VERY_HIGH';
  else if (waitingCount > 8) congestionLevel = 'HIGH';
  else if (waitingCount > 3) congestionLevel = 'MODERATE';

  return NextResponse.json({
    centre_id: cId,
    centre_name: centre?.name || `Centre ${cId}`,
    total_in_queue: tokens.length,
    waiting_count: waitingCount,
    processing_count: processingTokens.length,
    completed_today: completedTokens.length,
    no_show_count: noShowTokens.length,
    current_token: activeToken?.token_number || null,
    currently_serving_token: activeToken?.token_number || null,
    active_token: activeToken,
    estimated_wait_time_minutes: estWaitMins,
    avg_processing_minutes: centre?.avg_processing_minutes || 20,
    congestion_level: congestionLevel,
    queue: waitingTokens.slice(0, 30),
    tokens,
  });
}
