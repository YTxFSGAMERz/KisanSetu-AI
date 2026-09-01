import { NextResponse } from 'next/server';
import { CROPS } from '@/lib/server-store';

export async function GET() {
  return NextResponse.json(CROPS);
}
