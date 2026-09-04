import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

export async function GET() {
  const token = dbStore.queue_tokens.find(t => t.status !== 'COMPLETED') || dbStore.queue_tokens[0];
  const booking = dbStore.bookings.find(b => b.farmer_id === 1) || dbStore.bookings[0];

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
    total_amount_received: dbStore.payments.reduce((s, p) => s + p.amount, 0),
    total_procurements_count: dbStore.procurements.length,
    active_bookings_count: dbStore.bookings.filter(b => b.booking_status === 'CONFIRMED').length,
    unread_notifications: dbStore.notifications.filter(n => !n.is_read).length,
    current_token: token ? {
      ...token,
      centre_name: 'Karnal Grain Mandi',
    } : null,
    upcoming_slot: booking ? {
      booking_id: booking.id,
      booking_number: booking.booking_number,
      centre_name: booking.centre_name || 'Karnal Grain Mandi',
      slot_date: booking.slot_date,
      start_time: '09:00 AM',
      end_time: '11:00 AM',
      crop_name: booking.crop_name || 'Wheat',
      expected_quantity: booking.expected_quantity,
    } : null,
    recent_bookings: dbStore.bookings.slice(0, 5),
    recent_procurements: dbStore.procurements.slice(0, 5),
  });
}
