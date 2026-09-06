'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/auth-context';
import { procurementsApi } from '@/lib/api';
import ProcurementReceiptModal from '@/components/ProcurementReceiptModal';
import PaymentStatusModal from '@/components/PaymentStatusModal';

export default function ProcurementsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [procurements, setProcurements] = useState<any[]>([]);
  const [fetching, setFetching] = useState(true);
  const [selectedReceipt, setSelectedReceipt] = useState<any | null>(null);
  const [selectedPayment, setSelectedPayment] = useState<any | null>(null);

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  useEffect(() => {
    procurementsApi.my().then(setProcurements).catch(console.error).finally(() => setFetching(false));
  }, []);

  const statusColors: Record<string, string> = {
    PENDING: 'bg-gray-100 text-gray-600',
    IN_PROGRESS: 'bg-blue-100 text-blue-700',
    COMPLETED: 'bg-green-100 text-green-700',
    REJECTED: 'bg-red-100 text-red-700',
  };
  const gradeColors: Record<string, string> = {
    GRADE_A: 'bg-green-100 text-green-700',
    STANDARD: 'bg-amber-100 text-amber-700',
    BELOW_STANDARD: 'bg-red-100 text-red-700',
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <button onClick={() => router.push('/farmer')} className="text-green-700">← Back</button>
          <h1 className="font-bold text-gray-900">My Procurements</h1>
        </div>
      </div>
      <div className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {fetching && <div className="text-center text-gray-400 py-8 animate-pulse">Loading procurements...</div>}
        {!fetching && procurements.length === 0 && (
          <div className="bg-white rounded-2xl p-8 text-center border border-gray-200">
            <p className="text-4xl mb-3">📦</p>
            <p className="text-gray-600">No procurement records yet.</p>
            <button onClick={() => router.push('/farmer/book-slot')} className="mt-4 bg-green-700 text-white px-5 py-2 rounded-lg text-sm font-medium">Book a Slot</button>
          </div>
        )}
        {procurements.map((p) => {
          const isWheat = p.crop_name?.toLowerCase().includes('wheat');
          const isMustard = p.crop_name?.toLowerCase().includes('mustard') || p.crop_name?.toLowerCase().includes('sarson');
          const cropIcon = isWheat ? '🌾' : isMustard ? '🟡' : '🌾';
          const formattedDate = p.created_at
            ? new Date(p.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
            : 'Recent';

          return (
            <div key={p.id} className="bg-white rounded-2xl p-5 border border-gray-200 hover:border-green-300 transition-all shadow-xs">
              <div className="flex items-start justify-between mb-3.5">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl bg-green-50 border border-green-200 flex items-center justify-center text-xl shrink-0">
                    {cropIcon}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-bold text-gray-900 text-base">{p.crop_name || 'Produce'}</p>
                      <span className="font-mono text-xs bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded-md font-semibold">
                        J-Form: {p.receipt_number || `JF-HR-KNL-2026-${String(p.id).padStart(5, '0')}`}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1 flex items-center gap-1.5 flex-wrap">
                      <span>📍 {p.centre_name || 'Karnal Grain Mandi'}</span>
                      <span>•</span>
                      <span>{formattedDate}</span>
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${statusColors[p.status] || 'bg-gray-100 text-gray-600'}`}>
                    {p.status === 'COMPLETED' ? '✓ Procurement Completed' : p.status.replace('_', ' ')}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 text-sm">
                <div className="bg-slate-50 border border-slate-100 rounded-xl p-2.5">
                  <p className="text-xs text-slate-600 font-medium">Accepted Qty</p>
                  <p className="font-bold text-slate-900 mt-0.5">{p.accepted_quantity ?? '—'} Qtl</p>
                </div>
                <div className="bg-slate-50 border border-slate-100 rounded-xl p-2.5">
                  <p className="text-xs text-slate-600 font-medium">Rejection</p>
                  <p className="font-bold text-slate-700 mt-0.5">{p.rejected_quantity ?? 0} Qtl</p>
                </div>
                <div className="bg-slate-50 border border-slate-100 rounded-xl p-2.5">
                  <p className="text-xs text-slate-600 font-medium mb-1">Quality Inspection</p>
                  {p.quality_grade ? (
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-md ${gradeColors[p.quality_grade] || 'bg-green-100 text-green-700'}`}>
                      {p.quality_grade === 'GRADE_A' ? 'Grade A (FAQ)' : p.quality_grade.replace('_', ' ')}
                    </span>
                  ) : <p className="text-slate-400 text-xs">Pending</p>}
                </div>
              </div>

              {p.procurement_amount && (
                <div
                  onClick={() => setSelectedPayment({
                    id: p.id,
                    amount: p.procurement_amount,
                    status: 'COMPLETED',
                    crop_name: p.crop_name,
                    centre_name: p.centre_name,
                    receipt_number: p.receipt_number,
                    accepted_quantity: p.accepted_quantity,
                    quality_grade: p.quality_grade,
                    completed_at: p.completed_at || p.created_at,
                    farmer_name: user?.name || p.farmer_name,
                  })}
                  className="mt-3.5 bg-green-50 hover:bg-green-100/80 border border-green-200/80 rounded-xl p-3 flex items-center justify-between cursor-pointer transition-colors group/pay"
                  title="Click to view detailed PFMS DBT payment status card"
                >
                  <div>
                    <span className="text-xs text-green-800 font-semibold block group-hover/pay:underline">
                      Settlement Amount (CACP MSP) ↗
                    </span>
                    <span className="text-[11px] text-green-700">
                      {p.accepted_quantity} Qtl {p.msp_per_quintal ? `@ ₹${Number(p.msp_per_quintal).toLocaleString('en-IN')}/Qtl` : ''}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-xl font-extrabold text-green-800 font-mono">₹{p.procurement_amount.toLocaleString('en-IN')}</span>
                    <span className="text-[10px] bg-green-200/80 text-green-900 font-bold px-1.5 py-0.5 rounded block mt-0.5">
                      ✓ PFMS DBT Processed
                    </span>
                  </div>
                </div>
              )}

              <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-2xs">
                <button
                  type="button"
                  onClick={() => setSelectedReceipt(p)}
                  className="text-blue-700 hover:text-blue-900 font-bold inline-flex items-center gap-1 cursor-pointer hover:underline"
                >
                  <span>📜</span>
                  <span>View Official J-Form Receipt</span>
                </button>
                {p.procurement_amount && (
                  <button
                    type="button"
                    onClick={() => setSelectedPayment({
                      id: p.id,
                      amount: p.procurement_amount,
                      status: 'COMPLETED',
                      crop_name: p.crop_name,
                      centre_name: p.centre_name,
                      receipt_number: p.receipt_number,
                      accepted_quantity: p.accepted_quantity,
                      quality_grade: p.quality_grade,
                      completed_at: p.completed_at || p.created_at,
                      farmer_name: user?.name || p.farmer_name,
                    })}
                    className="text-emerald-700 hover:text-emerald-900 font-bold inline-flex items-center gap-1 cursor-pointer hover:underline"
                  >
                    <span>💳</span>
                    <span>View DBT Payment Card →</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* J-Form Digital Receipt Modal */}
      <ProcurementReceiptModal
        isOpen={Boolean(selectedReceipt)}
        receipt={selectedReceipt}
        onClose={() => setSelectedReceipt(null)}
      />

      {/* Payment Status Card Pop-up */}
      <PaymentStatusModal
        isOpen={Boolean(selectedPayment)}
        payment={selectedPayment}
        onClose={() => setSelectedPayment(null)}
        farmerName={user?.name || selectedPayment?.farmer_name}
      />
    </div>
  );
}
