import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

export async function POST(req: Request) {
  try {
    const url = new URL(req.url);
    const centreId = Number(url.searchParams.get('centre_id') || 1);

    const nextWaiting = dbStore.queue_tokens.find(t => t.centre_id === centreId && t.status === 'WAITING');
    if (!nextWaiting) {
      return NextResponse.json({ detail: 'No farmers waiting in queue' }, { status: 404 });
    }

    nextWaiting.status = 'CALLED';
    nextWaiting.called_at = new Date().toISOString();

    // Add notification
    dbStore.notifications.unshift({
      id: dbStore.notifications.length + 1,
      user_id: 1,
      title: `Token ${nextWaiting.token_number} Called! 📢`,
      message: `Your token ${nextWaiting.token_number} is now called! Please proceed to Counter 1.`,
      type: 'TOKEN_CALLED',
      channel: 'IN_APP',
      is_read: false,
      created_at: new Date().toISOString(),
    });

    return NextResponse.json(nextWaiting);
  } catch (error: any) {
    return NextResponse.json({ detail: error.message || 'Action failed' }, { status: 400 });
  }
}
