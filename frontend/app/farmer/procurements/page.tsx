'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/auth-context';
import { procurementsApi } from '@/lib/api';

export default function ProcurementsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [procurements, setProcurements] = useState<any[]>([]);
  const [fetching, setFetching] = useState(true);

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
        {procurements.map((p) => (
          <div key={p.id} className="bg-white rounded-2xl p-5 border border-gray-200">
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="font-bold text-gray-900">{p.crop_name}</p>
                <p className="text-xs text-gray-500">{p.receipt_number || `Procurement #${p.id}`}</p>
                <p className="text-xs text-gray-400">{p.centre_name}</p>
              </div>
              <div className="text-right">
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${statusColors[p.status] || 'bg-gray-100 text-gray-600'}`}>
                  {p.status.replace('_', ' ')}
                </span>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3 text-sm">
              <div className="bg-gray-50 rounded-lg p-2">
                <p className="text-xs text-gray-400">Accepted</p>
                <p className="font-semibold">{p.accepted_quantity ?? '—'} Qtl</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-2">
                <p className="text-xs text-gray-400">Rejected</p>
                <p className="font-semibold text-red-600">{p.rejected_quantity ?? 0} Qtl</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-2">
                <p className="text-xs text-gray-400">Grade</p>
                {p.quality_grade ? (
                  <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${gradeColors[p.quality_grade]}`}>{p.quality_grade.replace('_', ' ')}</span>
                ) : <p className="text-gray-400 text-xs">Pending</p>}
              </div>
            </div>
            {p.procurement_amount && (
              <div className="mt-3 bg-green-50 rounded-lg p-3 flex items-center justify-between">
                <span className="text-sm text-green-700 font-medium">MSP Amount</span>
                <span className="text-lg font-bold text-green-800">₹{p.procurement_amount.toLocaleString('en-IN')}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
