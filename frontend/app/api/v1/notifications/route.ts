import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

export async function GET(req: Request) {
  const url = new URL(req.url);
  const userId = url.searchParams.get('user_id');

  let results = [...dbStore.notifications];
  if (userId) {
    results = results.filter(n => n.user_id === Number(userId));
  }

  return NextResponse.json(results);
}
