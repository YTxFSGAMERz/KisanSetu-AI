import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

/**
 * POST / PUT /api/v1/queue/[id]/complete
 * Marks a queue token as COMPLETED (officer action)
 * `id` here can be the token ID or booking ID
 */
export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  return handleComplete(req, params);
}

export async function PUT(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  return handleComplete(req, params);
}

async function handleComplete(
  req: Request,
  params: Promise<{ id: string }>
) {
  const { id } = await params;
  const numId = Number(id);
  const token = dbStore.queue_tokens.find(t => t.id === numId || t.booking_id === numId);
  if (!token) {
    return NextResponse.json({ detail: 'Token not found' }, { status: 404 });
  }

  token.status = 'COMPLETED';
  token.completed_at = new Date().toISOString();

  // Mark associated booking as COMPLETED
  const booking = dbStore.bookings.find(b => b.id === token.booking_id);
  if (booking) {
    booking.booking_status = 'COMPLETED';
  }

  return NextResponse.json(token);
}
