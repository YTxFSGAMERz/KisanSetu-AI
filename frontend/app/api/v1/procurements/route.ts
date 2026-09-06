import { NextResponse } from 'next/server';
import { dbStore, CROPS } from '@/lib/server-store';

export async function GET(req: Request) {
  const url = new URL(req.url);
  const bookingId = url.searchParams.get('booking_id');
  const centreId = url.searchParams.get('centre_id');

  let results = [...dbStore.procurements];
  if (bookingId) {
    results = results.filter(p => p.booking_id === Number(bookingId));
  }
  if (centreId) {
    const cid = Number(centreId);
    const centreBookings = new Set(
      dbStore.bookings.filter(b => b.centre_id === cid).map(b => b.id)
    );
    results = results.filter(p => centreBookings.has(p.booking_id) || (cid === 1 && (!p.centre_name || p.centre_name.includes('Karnal'))));
  }

  // Always return newest first
  results.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime());

  return NextResponse.json(results);
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const {
      booking_id,
      actual_quantity,
      accepted_quantity,
      rejected_quantity = 0,
      quality_grade = 'GRADE_A',
      notes,
    } = body;

    const existing = dbStore.procurements.find(p => p.booking_id === Number(booking_id));
    if (existing) {
      return NextResponse.json({ detail: "Procurement record already exists for this booking" }, { status: 409 });
    }

    const booking = dbStore.bookings.find(b => b.id === Number(booking_id)) || dbStore.bookings[0];
    const crop = CROPS.find(c => c.id === booking.crop_id) || CROPS[0];

    const priceMultiplier = quality_grade === 'GRADE_A' ? 1.0 : quality_grade === 'STANDARD' ? 0.95 : 0.85;
    const finalRate = crop.msp_per_quintal * priceMultiplier;
    const procurementAmount = Number((Number(accepted_quantity) * finalRate).toFixed(2));

    const nextId = dbStore.procurements.length + 1;
    const receiptNum = `RCP-KNL-2026-${String(nextId).padStart(4, '0')}`;

    const newProcurement = {
      id: nextId,
      booking_id: booking.id,
      crop_id: crop.id,
      crop_name: crop.name,
      farmer_name: booking.farmer_name || 'Rajesh Verma',
      centre_name: booking.centre_name || 'Karnal Grain Mandi',
      booking_number: booking.booking_number,
      expected_quantity: booking.expected_quantity,
      actual_quantity: Number(actual_quantity),
      accepted_quantity: Number(accepted_quantity),
      rejected_quantity: Number(rejected_quantity),
      quality_grade: quality_grade as any,
      procurement_amount: procurementAmount,
      status: 'COMPLETED' as const,
      receipt_number: receiptNum,
      created_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
    };

    dbStore.procurements.unshift(newProcurement);

    // Also generate pending payment
    const newPayment = {
      id: dbStore.payments.length + 1,
      procurement_id: newProcurement.id,
      amount: procurementAmount,
      status: 'PENDING' as const,
      farmer_name: newProcurement.farmer_name,
      crop_name: newProcurement.crop_name,
      receipt_number: receiptNum,
      created_at: new Date().toISOString(),
    };
    dbStore.payments.unshift(newPayment);

    // Update booking status and complete queue token
    booking.booking_status = 'COMPLETED';
    const queueTok = dbStore.queue_tokens.find(t => t.booking_id === booking.id || t.id === booking.id);
    if (queueTok) {
      queueTok.status = 'COMPLETED';
      queueTok.completed_at = new Date().toISOString();
    }

    return NextResponse.json(newProcurement, { status: 201 });
  } catch (error: any) {
    return NextResponse.json({ detail: error.message || 'Procurement creation failed' }, { status: 400 });
  }
}
