import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const procurement = dbStore.procurements.find(p => p.id === Number(id));
  if (!procurement) {
    return NextResponse.json({ detail: 'Procurement not found' }, { status: 404 });
  }
  return NextResponse.json(procurement);
}
