import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

export async function GET(req: Request) {
  const url = new URL(req.url);
  const centreId = url.searchParams.get('centre_id');
  const date = url.searchParams.get('date');

  let slots = dbStore.slots || [];
  if (centreId) {
    slots = slots.filter(s => s.centre_id === Number(centreId));
  }
  if (date) {
    slots = slots.filter(s => s.slot_date === date);
  }
  return NextResponse.json(slots);
}
