import { NextResponse } from 'next/server';
import { dbStore, CENTRES } from '@/lib/server-store';

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const centreId = parseInt(id, 10);
  const centre = CENTRES.find(c => c.id === centreId) || CENTRES[0];

  const slots = dbStore.slots.filter(s => s.centre_id === centreId);

  return NextResponse.json({
    centre_id: centre.id,
    centre_name: centre.name,
    available_slots_count: slots.length,
    slots,
  });
}
