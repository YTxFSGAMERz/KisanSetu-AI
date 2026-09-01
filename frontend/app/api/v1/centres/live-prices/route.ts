import { NextResponse } from 'next/server';
import { LIVE_PRICES } from '@/lib/server-store';

export async function GET() {
  return NextResponse.json(LIVE_PRICES);
}
