'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/auth-context';
import { paymentsApi } from '@/lib/api';
import PaymentStatusModal from '@/components/PaymentStatusModal';

export default function PaymentsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [payments, setPayments] = useState<any[]>([]);
  const [fetching, setFetching] = useState(true);
  const [selectedPayment, setSelectedPayment] = useState<any | null>(null);

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
    <div className="min-h-screen bg-gray-50 pb-12">
      <div className="bg-white border-b px-4 py-3 sticky top-0 z-10 shadow-2xs">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/farmer')}
              className="text-green-700 hover:text-green-900 font-bold flex items-center gap-1 text-sm cursor-pointer"
            >
              ← Back
            </button>
            <h1 className="font-bold text-gray-900">Payment Status</h1>
          </div>
          <span className="text-2xs font-semibold px-2.5 py-1 bg-green-50 text-green-700 border border-green-200 rounded-full">
            PFMS DBT Verified
          </span>
        </div>
      </div>
      <div className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {/* Summary */}
        <div className="bg-gradient-to-r from-green-700 to-emerald-600 rounded-2xl p-5 text-white shadow-md relative overflow-hidden">
          <div className="absolute top-3 right-4 text-5xl opacity-15 select-none pointer-events-none">
            🏛️
          </div>
          <p className="text-green-100 text-sm font-medium">Total Amount Received (Direct DBT)</p>
          <p className="text-4xl font-extrabold mt-1 font-mono">₹{totalReceived.toLocaleString('en-IN')}</p>
          <div className="flex flex-wrap items-center justify-between gap-2 mt-3 pt-3 border-t border-white/20 text-xs text-green-100">
            <span>{payments.filter(p => p.status === 'COMPLETED').length} of {payments.length} payments completed</span>
            <span className="text-2xs bg-white/20 px-2.5 py-0.5 rounded-full font-medium">
              Aadhaar Seeded DBT Bank Account
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-slate-500 px-1">
          <span className="font-semibold text-slate-700">Procurement Payment Records ({payments.length})</span>
          <span className="text-2xs text-slate-400">Tap any record to view detailed card pop-up</span>
        </div>

        {fetching && (
          <div className="bg-white rounded-2xl p-10 text-center text-gray-400 border border-gray-200 shadow-xs">
            <div className="text-3xl animate-spin mb-2">🔄</div>
            <p className="text-sm font-medium">Fetching PFMS payment records...</p>
          </div>
        )}
        {!fetching && payments.length === 0 && (
          <div className="bg-white rounded-2xl p-8 text-center border border-gray-200">
            <p className="text-4xl mb-3">💰</p>
            <p className="text-gray-600">No payment records yet.</p>
          </div>
        )}
        {payments.map((p) => {
          const cfg = statusConfig[p.status] || statusConfig.PENDING;
          const isWheat = p.crop_name?.toLowerCase().includes('wheat');
          const isMustard = p.crop_name?.toLowerCase().includes('mustard') || p.crop_name?.toLowerCase().includes('sarson');
          const cropIcon = isWheat ? '🌾' : isMustard ? '🟡' : '🌾';

          return (
            <div
              key={p.id}
              onClick={() => setSelectedPayment(p)}
              className="bg-white rounded-2xl p-5 border border-gray-200 hover:border-green-400 hover:shadow-md transition-all shadow-xs cursor-pointer group active:scale-[0.995]"
              title="Click to view full payment status card pop up"
            >
              <div className="flex items-start justify-between mb-3.5">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl bg-green-50 border border-green-200 flex items-center justify-center text-xl shrink-0 group-hover:scale-105 transition-transform">
                    {cropIcon}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-bold text-gray-900 text-base group-hover:text-green-800 transition-colors">
                        {p.crop_name || 'Procurement Settlement'}
                      </p>
                      <span className="font-mono text-xs bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded-md font-semibold">
                        J-Form: {p.receipt_number || `JF-HR-KNL-2026-${String(p.id).padStart(5, '0')}`}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">📍 {p.centre_name || 'Karnal Grain Mandi'}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-extrabold text-green-700 font-mono">₹{p.amount.toLocaleString('en-IN')}</p>
                  <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full mt-1 ${cfg.color}`}>
                    <span>{cfg.icon}</span> {p.status === 'COMPLETED' ? 'PFMS DBT Credited' : p.status}
                  </span>
                </div>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs space-y-1.5">
                {p.transaction_reference && (
                  <div className="flex items-center justify-between text-slate-700 font-mono">
                    <span className="text-slate-500 font-sans">PFMS DBT UTR:</span>
                    <span className="font-semibold text-slate-900">{p.transaction_reference}</span>
                  </div>
                )}
                <div className="flex items-center justify-between text-slate-700">
                  <span className="text-slate-500">Credited To:</span>
                  <span className="font-medium text-slate-800">HDFC Bank •••• 1012 (Aadhaar Seeded A/c)</span>
                </div>
                {p.completed_at && (
                  <div className="flex items-center justify-between text-slate-700">
                    <span className="text-slate-500">Settled On:</span>
                    <span className="font-medium text-emerald-700">
                      {new Date(p.completed_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}
                    </span>
                  </div>
                )}
              </div>

              {/* Card Pop-up Click Hint */}
              <div className="pt-2.5 mt-2.5 border-t border-slate-100 flex items-center justify-between text-2xs text-green-700 font-semibold">
                <span className="group-hover:underline flex items-center gap-1">
                  <span>💳</span>
                  <span>View Full Payment Status & DBT Advice Card</span>
                </span>
                <span className="text-slate-400 group-hover:text-green-700 group-hover:translate-x-0.5 transition-all">
                  Details →
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Interactive Payment Status Card Pop-up */}
      <PaymentStatusModal
        isOpen={Boolean(selectedPayment)}
        payment={selectedPayment}
        onClose={() => setSelectedPayment(null)}
        farmerName={user?.name || selectedPayment?.farmer_name}
      />
    </div>
  );
}
