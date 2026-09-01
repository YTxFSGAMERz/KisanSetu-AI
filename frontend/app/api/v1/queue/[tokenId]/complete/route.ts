import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

export async function PUT(
  req: Request,
  { params }: { params: Promise<{ tokenId: string }> }
) {
  const { tokenId } = await params;
  const token = dbStore.queue_tokens.find(t => t.id === Number(tokenId));
  if (!token) {
    return NextResponse.json({ detail: 'Token not found' }, { status: 404 });
  }

  token.status = 'COMPLETED';
  token.completed_at = new Date().toISOString();

  return NextResponse.json(token);
}
