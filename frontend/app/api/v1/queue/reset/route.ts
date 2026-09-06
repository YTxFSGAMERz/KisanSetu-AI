import { NextResponse } from 'next/server';
import { dbStore, CENTRES, CROPS } from '@/lib/server-store';

const INITIAL_ROSTER = [
  { token: 'A001', name: 'Sukhwinder Singh', crop: 'Wheat', qty: 50, status: 'WAITING' },
  { token: 'A002', name: 'Ramesh Kumar Yadav', crop: 'Mustard / Rapeseed', qty: 30, status: 'WAITING' },
  { token: 'A003', name: 'Gurpreet Kaur Sandhu', crop: 'Wheat', qty: 45, status: 'WAITING' },
  { token: 'A004', name: 'Tejpal Singh Beniwal', crop: 'Gram (Chickpea)', qty: 25, status: 'WAITING' },
  { token: 'A005', name: 'Baldev Raj Arora', crop: 'Wheat', qty: 60, status: 'WAITING' },
  { token: 'A006', name: 'Parvati Devi Choudhary', crop: 'Mustard / Rapeseed', qty: 20, status: 'WAITING' },
  { token: 'A007', name: 'Manjeet Singh Dhaliwal', crop: 'Wheat', qty: 40, status: 'WAITING' },
  { token: 'A008', name: 'Amarjit Singh Bajwa', crop: 'Wheat', qty: 35, status: 'WAITING' },
  { token: 'A009', name: 'Rajesh Verma (Kisan)', crop: 'Wheat', qty: 40, status: 'WAITING' },
  { token: 'A010', name: 'Harishchandra Lal Meena', crop: 'Mustard / Rapeseed', qty: 30, status: 'WAITING' },
  { token: 'A011', name: 'Prakash Narayan Patel', crop: 'Wheat', qty: 50, status: 'WAITING' },
  { token: 'A012', name: 'Vijay Bhagwan Deshmukh', crop: 'Mustard / Rapeseed', qty: 35, status: 'WAITING' },
  { token: 'A013', name: 'Shantabai Kisanrao Patil', crop: 'Gram (Chickpea)', qty: 25, status: 'WAITING' },
  { token: 'A014', name: 'Hardev Singh Gill', crop: 'Wheat', qty: 60, status: 'WAITING' },
  { token: 'A015', name: 'Pushpabai Vithalrao Jadhav', crop: 'Soybean (Yellow)', qty: 40, status: 'WAITING' },
];

export async function POST(req: Request) {
  try {
    const url = new URL(req.url);
    const centreId = Number(url.searchParams.get('centre_id') || 1);

    // Remove existing tokens for this centre
    const filtered = dbStore.queue_tokens.filter((t) => t.centre_id !== centreId);
    dbStore.queue_tokens.length = 0;
    dbStore.queue_tokens.push(...filtered);

    // Re-seed fresh waiting tokens
    INITIAL_ROSTER.forEach((item, idx) => {
      dbStore.queue_tokens.push({
        id: dbStore.queue_tokens.length + 1,
        booking_id: idx + 1,
        centre_id: centreId,
        token_number: item.token,
        queue_position: idx + 1,
        status: 'WAITING' as const,
        estimated_wait_minutes: (idx + 1) * 15,
        farmer_name: item.name,
        crop_name: item.crop,
        expected_quantity: item.qty,
        farmers_ahead: idx,
        arrival_time: new Date().toISOString(),
        called_at: null,
      });
    });

    return NextResponse.json({
      success: true,
      message: `Reset queue with ${INITIAL_ROSTER.length} waiting farmers`,
      queue_count: INITIAL_ROSTER.length,
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || 'Failed to reset queue' }, { status: 400 });
  }
}
