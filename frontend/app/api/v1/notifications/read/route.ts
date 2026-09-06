import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const ids: number[] = body.notification_ids || [];
    if (ids.length > 0) {
      dbStore.notifications.forEach((n) => {
        if (ids.includes(n.id)) {
          n.is_read = true;
        }
      });
    }
    return NextResponse.json({ marked_read: ids.length });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
