import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

export async function GET(
  req: Request,
  { params }: { params: Promise<{ farmerId: string }> }
) {
  const { farmerId } = await params;
  const bookings = dbStore.bookings.filter(b => b.farmer_id === Number(farmerId));
  return NextResponse.json(bookings);
}
