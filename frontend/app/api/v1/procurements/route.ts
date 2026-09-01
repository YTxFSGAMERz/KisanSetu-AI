import { NextResponse } from 'next/server';
import { dbStore, CROPS } from '@/lib/server-store';

export async function GET(req: Request) {
  const url = new URL(req.url);
  const bookingId = url.searchParams.get('booking_id');

  let results = [...dbStore.procurements];
  if (bookingId) {
    results = results.filter(p => p.booking_id === Number(bookingId));
  }

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

    // Update booking status
    booking.booking_status = 'COMPLETED';

    return NextResponse.json(newProcurement, { status: 201 });
  } catch (error: any) {
    return NextResponse.json({ detail: error.message || 'Procurement creation failed' }, { status: 400 });
  }
}
