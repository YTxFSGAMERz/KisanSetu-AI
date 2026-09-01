import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

export async function PUT(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const notif = dbStore.notifications.find(n => n.id === Number(id));
  if (!notif) {
    return NextResponse.json({ detail: 'Notification not found' }, { status: 404 });
  }

  notif.is_read = true;
  return NextResponse.json(notif);
}
