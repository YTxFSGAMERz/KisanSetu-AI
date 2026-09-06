import { NextResponse } from 'next/server';
import { dbStore, CENTRES, CROPS } from '@/lib/server-store';

const FARMER_NAMES = [
  'Sukhwinder Singh',
  'Ramesh Kumar Yadav',
  'Gurpreet Kaur Sandhu',
  'Tejpal Singh Beniwal',
  'Baldev Raj Arora',
  'Parvati Devi Choudhary',
  'Manjeet Singh Dhaliwal',
  'Amarjit Singh Bajwa',
  'Harishchandra Lal Meena',
  'Prakash Narayan Patel',
  'Vijay Bhagwan Deshmukh',
  'Shantabai Kisanrao Patil',
  'Hardev Singh Gill',
  'Pushpabai Vithalrao Jadhav',
  'Jagdish Prasad Gupta',
  'Lalita Bai Thakur',
  'Kamlavati Ramnarayan Sharma',
  'Ranjit Kumar Mahato',
  'Sunita Devi Yadav',
];

export async function POST(req: Request) {
  try {
    const url = new URL(req.url);
    const centreId = Number(url.searchParams.get('centre_id') || 1);
    const count = Math.min(20, Math.max(1, Number(url.searchParams.get('count') || 10)));

    const centre = CENTRES.find((c) => c.id === centreId) || CENTRES[0];
    const existingTokens = dbStore.queue_tokens.filter((t) => t.centre_id === centreId);
    
    // Find current highest token number (e.g. A010 -> 10)
    let highestNumber = 0;
    for (const t of existingTokens) {
      const numMatch = t.token_number.match(/\d+/);
      if (numMatch) {
        const n = parseInt(numMatch[0], 10);
        if (n > highestNumber) highestNumber = n;
      }
    }

    const currentWaitingCount = existingTokens.filter((t) => t.status === 'WAITING').length;
    let nextPos = currentWaitingCount + 1;
    const addedTokens = [];

    for (let i = 0; i < count; i++) {
      highestNumber++;
      const tokenNum = `A${String(highestNumber).padStart(3, '0')}`;
      const farmerName = FARMER_NAMES[(highestNumber - 1) % FARMER_NAMES.length];
      const crop = CROPS[(highestNumber - 1) % CROPS.length];
      const qty = [25, 30, 35, 40, 45, 50, 55, 60][(highestNumber - 1) % 8];

      const maxBookingId = dbStore.bookings.length + 1;
      const bNum = `BK-${centre.code.split('-')[2] || 'KNL'}-2026-${String(maxBookingId).padStart(4, '0')}`;

      const booking = {
        id: maxBookingId,
        booking_number: bNum,
        farmer_id: ((highestNumber - 1) % 20) + 1,
        farmer_name: farmerName,
        centre_id: centre.id,
        centre_name: centre.name,
        slot_id: 1,
        slot_date: new Date().toISOString().split('T')[0],
        slot_time: '13:00 - 15:00',
        crop_id: crop.id,
        crop_name: crop.name,
        expected_quantity: qty,
        booking_status: 'CONFIRMED' as const,
        token_number: tokenNum,
        queue_position: nextPos,
        estimated_wait_minutes: nextPos * (centre.avg_processing_minutes || 15),
        notes: `${crop.name} ${qty} Quintals`,
        created_at: new Date().toISOString(),
      };
      dbStore.bookings.push(booking);

      const token = {
        id: dbStore.queue_tokens.length + 1,
        booking_id: booking.id,
        centre_id: centre.id,
        token_number: tokenNum,
        queue_position: nextPos,
        status: 'WAITING' as const,
        estimated_wait_minutes: nextPos * (centre.avg_processing_minutes || 15),
        farmer_name: farmerName,
        crop_name: crop.name,
        expected_quantity: qty,
        farmers_ahead: nextPos - 1,
        arrival_time: new Date().toISOString(),
        called_at: null,
      };
      dbStore.queue_tokens.push(token);
      addedTokens.push(token);
      nextPos++;
    }

    return NextResponse.json({
      success: true,
      message: `Added ${addedTokens.length} farmers to the waiting queue`,
      added: addedTokens,
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || 'Failed to add farmers' }, { status: 400 });
  }
}
