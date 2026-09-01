import { NextResponse } from 'next/server';
import { CENTRES } from '@/lib/server-store';

export async function GET(req: Request) {
  const url = new URL(req.url);
  const state = url.searchParams.get('state');
  const district = url.searchParams.get('district');

  let results = [...CENTRES];
  if (state) {
    results = results.filter(c => c.state.toLowerCase() === state.toLowerCase());
  }
  if (district) {
    results = results.filter(c => c.district.toLowerCase() === district.toLowerCase());
  }

  return NextResponse.json(results);
}
