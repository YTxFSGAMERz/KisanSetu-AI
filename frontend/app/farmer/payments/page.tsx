'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/auth-context';
import { paymentsApi } from '@/lib/api';

export default function PaymentsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [payments, setPayments] = useState<any[]>([]);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  useEffect(() => {
    paymentsApi.my().then(setPayments).catch(console.error).finally(() => setFetching(false));
  }, []);

  const totalReceived = payments.filter(p => p.status === 'COMPLETED').reduce((s, p) => s + p.amount, 0);

  const statusConfig: Record<string, { color: string; icon: string }> = {
    PENDING: { color: 'bg-gray-100 text-gray-600', icon: '⏳' },
    PROCESSING: { color: 'bg-blue-100 text-blue-700', icon: '🔄' },
    COMPLETED: { color: 'bg-green-100 text-green-700', icon: '✅' },
    FAILED: { color: 'bg-red-100 text-red-700', icon: '❌' },
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <button onClick={() => router.push('/farmer')} className="text-green-700">← Back</button>
          <h1 className="font-bold text-gray-900">Payment Status</h1>
        </div>
      </div>
      <div className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {/* Summary */}
        <div className="bg-gradient-to-r from-green-700 to-emerald-600 rounded-2xl p-5 text-white">
          <p className="text-green-100 text-sm">Total Amount Received</p>
          <p className="text-4xl font-bold mt-1">₹{totalReceived.toLocaleString('en-IN')}</p>
          <p className="text-green-200 text-xs mt-2">{payments.filter(p => p.status === 'COMPLETED').length} of {payments.length} payments completed</p>
        </div>

        {fetching && <div className="text-center text-gray-400 py-8 animate-pulse">Loading payments...</div>}
        {!fetching && payments.length === 0 && (
          <div className="bg-white rounded-2xl p-8 text-center border border-gray-200">
            <p className="text-4xl mb-3">💰</p>
            <p className="text-gray-600">No payment records yet.</p>
          </div>
        )}
        {payments.map((p) => {
          const cfg = statusConfig[p.status] || statusConfig.PENDING;
          return (
            <div key={p.id} className="bg-white rounded-2xl p-5 border border-gray-200">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="font-bold text-gray-900">{cfg.icon} {p.crop_name}</p>
                  <p className="text-xs text-gray-500">{p.receipt_number}</p>
                  <p className="text-xs text-gray-400">{p.centre_name}</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-green-700">₹{p.amount.toLocaleString('en-IN')}</p>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${cfg.color}`}>{p.status}</span>
                </div>
              </div>
              {p.transaction_reference && (
                <div className="bg-gray-50 rounded-lg p-2 text-xs text-gray-600 font-mono">
                  Txn: {p.transaction_reference}
                </div>
              )}
              {p.completed_at && (
                <p className="text-xs text-green-600 mt-2">Paid on {new Date(p.completed_at).toLocaleString('en-IN')}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
