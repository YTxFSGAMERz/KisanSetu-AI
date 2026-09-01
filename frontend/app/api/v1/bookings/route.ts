import { NextResponse } from 'next/server';
import { dbStore, CENTRES, CROPS } from '@/lib/server-store';

export async function GET(req: Request) {
  const url = new URL(req.url);
  const farmerId = url.searchParams.get('farmer_id');
  const centreId = url.searchParams.get('centre_id');

  let results = [...dbStore.bookings];
  if (farmerId) {
    results = results.filter(b => b.farmer_id === Number(farmerId));
  }
  if (centreId) {
    results = results.filter(b => b.centre_id === Number(centreId));
  }

  return NextResponse.json(results);
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { farmer_id = 1, centre_id, slot_id, crop_id, expected_quantity } = body;

    const centre = CENTRES.find(c => c.id === Number(centre_id)) || CENTRES[0];
    const crop = CROPS.find(c => c.id === Number(crop_id)) || CROPS[0];
    const slot = dbStore.slots.find(s => s.id === Number(slot_id)) || dbStore.slots[0];

    const nextId = dbStore.bookings.length + 1;
    const tokenNum = `A${String(nextId).padStart(3, '0')}`;
    const bookingNum = `BK-${centre.code.split('-')[2] || 'KNL'}-2026-${String(nextId).padStart(4, '0')}`;

    const newBooking = {
      id: nextId,
      booking_number: bookingNum,
      farmer_id: Number(farmer_id),
      farmer_name: 'Rajesh Verma',
      centre_id: centre.id,
      centre_name: centre.name,
      slot_id: slot.id,
      slot_date: slot.slot_date,
      slot_time: `${slot.start_time.slice(0, 5)} - ${slot.end_time.slice(0, 5)}`,
      crop_id: crop.id,
      crop_name: crop.name,
      expected_quantity: Number(expected_quantity),
      booking_status: 'CONFIRMED' as const,
      token_number: tokenNum,
      queue_position: dbStore.queue_tokens.filter(t => t.centre_id === centre.id && t.status === 'WAITING').length + 1,
      estimated_wait_minutes: 15.0 * nextId,
      created_at: new Date().toISOString(),
    };

    dbStore.bookings.unshift(newBooking);

    // Also add to queue tokens
    const newToken = {
      id: nextId,
      booking_id: newBooking.id,
      centre_id: centre.id,
      token_number: tokenNum,
      queue_position: newBooking.queue_position,
      status: 'WAITING' as const,
      estimated_wait_minutes: newBooking.estimated_wait_minutes,
      farmer_name: newBooking.farmer_name,
      crop_name: newBooking.crop_name,
      expected_quantity: newBooking.expected_quantity,
      farmers_ahead: Math.max(0, newBooking.queue_position - 1),
    };
    dbStore.queue_tokens.push(newToken);

    // Add in-app notification
    dbStore.notifications.unshift({
      id: dbStore.notifications.length + 1,
      user_id: 1,
      title: 'Slot Booked Successfully 🌾',
      message: `Your slot for ${crop.name} at ${centre.name} has been confirmed. Token: ${tokenNum}`,
      type: 'BOOKING_CONFIRMED',
      channel: 'IN_APP',
      is_read: false,
      created_at: new Date().toISOString(),
    });

    return NextResponse.json(newBooking, { status: 201 });
  } catch (error: any) {
    return NextResponse.json({ detail: error.message || 'Booking failed' }, { status: 400 });
  }
}
