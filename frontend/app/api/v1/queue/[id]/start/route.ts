import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

/**
 * POST / PUT /api/v1/queue/[id]/start
 * Marks a queue token as PROCESSING (officer begins processing)
 * `id` here is the token ID (not booking ID)
 */
export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  return handleStart(req, params);
}

export async function PUT(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  return handleStart(req, params);
}

async function handleStart(
  req: Request,
  params: Promise<{ id: string }>
) {
  const { id } = await params;
  const token = dbStore.queue_tokens.find(t => t.id === Number(id));
  if (!token) {
    return NextResponse.json({ detail: 'Token not found' }, { status: 404 });
  }

  token.status = 'PROCESSING';
  token.processing_start_time = new Date().toISOString();

  return NextResponse.json(token);
}
