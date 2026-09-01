import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

export async function GET(
  req: Request,
  { params }: { params: Promise<{ bookingId: string }> }
) {
  const { bookingId } = await params;
  const token = dbStore.queue_tokens.find(t => t.booking_id === Number(bookingId));
  if (!token) {
    return NextResponse.json({ detail: 'Queue token not found' }, { status: 404 });
  }
  return NextResponse.json(token);
}
