import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

export async function GET() {
  const results = [...dbStore.payments];
  results.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime());
  return NextResponse.json(results);
}
