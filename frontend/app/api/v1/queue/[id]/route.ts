import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

/**
 * GET /api/v1/queue/[id]
 * Returns queue token by booking ID (used by farmer live-queue page)
 */
export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const token = dbStore.queue_tokens.find(t => t.booking_id === Number(id));
  if (!token) {
    return NextResponse.json({ detail: 'Queue token not found' }, { status: 404 });
  }
  return NextResponse.json(token);
}
