import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const booking = dbStore.bookings.find(b => b.id === Number(id));
  if (!booking) {
    return NextResponse.json({ detail: 'Booking not found' }, { status: 404 });
  }
  return NextResponse.json(booking);
}
