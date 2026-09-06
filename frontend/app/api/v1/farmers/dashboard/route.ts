import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

export async function GET() {
  const farmerBookings = dbStore.bookings.filter(b => b.farmer_id === 1);
  const activeBooking = farmerBookings.find(b => b.booking_status === 'CONFIRMED') || farmerBookings[0];
  const token = dbStore.queue_tokens.find(t => t.booking_id === activeBooking?.id) || dbStore.queue_tokens[0];
  
  const farmerPayments = dbStore.payments.filter(p => p.farmer_name?.includes('Rajesh') || p.id <= 4);
  const totalAmountReceived = farmerPayments.filter(p => p.status === 'COMPLETED').reduce((s, p) => s + p.amount, 0);

  const farmerProcurements = dbStore.procurements
    .filter(p => p.farmer_name?.includes('Rajesh') || p.id <= 4)
    .slice(0, 5)
    .map(p => ({
      id: p.id,
      receipt_number: p.receipt_number,
      j_form_number: p.receipt_number,
      status: p.status,
      crop_name: p.crop_name || 'Wheat',
      centre_name: p.centre_name || 'Karnal Grain Mandi — Haryana State Agricultural Marketing Board',
      accepted_quantity: p.accepted_quantity,
      procurement_amount: p.procurement_amount,
      msp_rate: p.crop_name?.includes('Mustard') ? 5650.0 : p.crop_name?.includes('Paddy') ? 2300.0 : 2275.0,
      quality_grade: p.quality_grade || 'GRADE_A',
      created_at: p.created_at,
      payment_status: 'COMPLETED',
      transaction_reference: p.id === 1 ? 'PFMS-DBT-2026-9821034' : `PFMS-DBT-2026-${9481920 + p.id}`,
    }));

  return NextResponse.json({
    farmer: {
      id: 1,
      user_id: 1,
      farmer_registration_number: 'FRN-HR-2026-0042',
      aadhaar_last_four: '9012',
      land_size_acres: 12.5,
      preferred_language: 'hi',
      village: 'Kachhwa',
      district: 'Karnal',
      state: 'Haryana',
      bank_account_verified: true,
    },
    total_amount_received: totalAmountReceived || 485800.0,
    total_procurements_count: farmerProcurements.length,
    active_bookings_count: farmerBookings.filter(b => b.booking_status === 'CONFIRMED').length,
    unread_notifications: dbStore.notifications.filter(n => !n.is_read).length,
    current_token: token ? {
      ...token,
      centre_name: 'Karnal Grain Mandi — Haryana State Agricultural Marketing Board',
    } : null,
    upcoming_slot: activeBooking ? {
      booking_id: activeBooking.id,
      booking_number: activeBooking.booking_number,
      centre_name: activeBooking.centre_name || 'Karnal Grain Mandi — Haryana State Agricultural Marketing Board',
      slot_date: activeBooking.slot_date,
      start_time: '09:00:00',
      end_time: '11:00:00',
      crop_name: activeBooking.crop_name || 'Wheat',
      expected_quantity: activeBooking.expected_quantity,
    } : null,
    recent_bookings: farmerBookings.slice(0, 5),
    recent_procurements: farmerProcurements,
  });
}
