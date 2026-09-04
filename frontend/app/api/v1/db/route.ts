import { NextResponse } from 'next/server';
import { db } from '@/lib/db';

export async function GET() {
  try {
    const stats = db.getStats();
    return NextResponse.json({
      success: true,
      ...stats,
    });
  } catch (error: any) {
    return NextResponse.json(
      {
        success: false,
        error: error.message || 'Failed to inspect database stats',
      },
      { status: 500 }
    );
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));
    if (body.action === 'reset' || body.action === undefined) {
      const freshState = db.reset();
      return NextResponse.json({
        success: true,
        message: 'KisanSetu database successfully re-seeded to factory demo state.',
        last_updated: freshState.last_updated,
        counts: {
          centres: freshState.centres.length,
          crops: freshState.crops.length,
          slots: freshState.slots.length,
          bookings: freshState.bookings.length,
          queue_tokens: freshState.queue_tokens.length,
          procurements: freshState.procurements.length,
          payments: freshState.payments.length,
          notifications: freshState.notifications.length,
        },
      });
    }

    return NextResponse.json(
      { success: false, detail: 'Unsupported action. Use {"action": "reset"}' },
      { status: 400 }
    );
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message || 'Database reset failed' },
      { status: 500 }
    );
  }
}
