import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

export async function GET(req: Request) {
  const url = new URL(req.url);
  const procurementId = url.searchParams.get('procurement_id');

  let results = [...dbStore.payments];
  if (procurementId) {
    results = results.filter(p => p.procurement_id === Number(procurementId));
  }

  return NextResponse.json(results);
}
