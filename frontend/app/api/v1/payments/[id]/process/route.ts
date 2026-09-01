import { NextResponse } from 'next/server';
import { dbStore } from '@/lib/server-store';

export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const payment = dbStore.payments.find(p => p.id === Number(id));
  if (!payment) {
    return NextResponse.json({ detail: 'Payment not found' }, { status: 404 });
  }

  payment.status = 'COMPLETED';
  payment.transaction_reference = `TXN-DBT-2026-${Math.floor(100000 + Math.random() * 900000)}`;
  payment.completed_at = new Date().toISOString();

  // Add notification
  dbStore.notifications.unshift({
    id: dbStore.notifications.length + 1,
    user_id: 1,
    title: 'Payment Credited ₹💰',
    message: `Payment of ₹${payment.amount.toLocaleString('en-IN')} has been transferred via PFMS/DBT to your bank account. Ref: ${payment.transaction_reference}`,
    type: 'PAYMENT_COMPLETED',
    channel: 'SMS',
    is_read: false,
    created_at: new Date().toISOString(),
  });

  return NextResponse.json(payment);
}
