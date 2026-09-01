'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/auth-context';
import { useWebSocket } from '@/context/websocket-context';
import { analyticsApi, queueApi, procurementsApi, paymentsApi, centresApi } from '@/lib/api';

export default function OfficerDashboard() {
  const { user, logout, loading } = useAuth();
  const { lastMessage, connectToQueue } = useWebSocket();
  const router = useRouter();

  const [centres, setCentres] = useState<any[]>([]);
  const [selectedCentreId, setSelectedCentreId] = useState<number | null>(null);
  const [dashboard, setDashboard] = useState<any>(null);
  const [queue, setQueue] = useState<any>(null);
  const [activeView, setActiveView] = useState<'dashboard' | 'queue' | 'procure'>('dashboard');
  const [processingToken, setProcessingToken] = useState<any>(null);
  const [procureForm, setProcureForm] = useState({ actual_quantity: '', accepted_quantity: '', rejected_quantity: '0', quality_grade: 'GRADE_A', rejection_reason: '' });
  const [procureSubmitting, setProcureSubmitting] = useState(false);
  const [procureResult, setProcureResult] = useState<any>(null);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!loading && !user) router.push('/login');
    if (!loading && user && user.role === 'FARMER') router.push('/farmer');
  }, [user, loading, router]);

  useEffect(() => {
    centresApi.list().then((cs) => {
      setCentres(cs);
      if (cs.length > 0) setSelectedCentreId(cs[0].id);
    }).catch(console.error);
  }, []);

  const loadData = useCallback(async (cId: number) => {
    try {
      const [dash, q] = await Promise.all([
        analyticsApi.officerDashboard(cId),
        queueApi.status(cId),
      ]);
      setDashboard(dash);
      setQueue(q);
    } catch (e) {
      console.error(e);
    } finally {
      setFetching(false);
    }
  }, []);

  useEffect(() => {
    if (selectedCentreId) {
      setFetching(true);
      loadData(selectedCentreId);
      connectToQueue(selectedCentreId);
    }
  }, [selectedCentreId]);

  // Real-time updates
  useEffect(() => {
    if (lastMessage?.event === 'QUEUE_UPDATED' && selectedCentreId) {
      loadData(selectedCentreId);
    }
  }, [lastMessage, selectedCentreId]);

  const callNext = async () => {
    if (!selectedCentreId) return;
    setError('');
    try {
      const token = await queueApi.callNext(selectedCentreId);
      alert(`✅ Called Token ${token.token_number} — ${token.farmer_name}`);
      loadData(selectedCentreId);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const startProcessing = async (tokenId: number) => {
    try {
      await queueApi.start(tokenId);
      const tok = queue?.queue?.find((t: any) => t.id === tokenId);
      setProcessingToken(tok);
      setProcureForm({ actual_quantity: String(tok?.expected_quantity || ''), accepted_quantity: String(tok?.expected_quantity || ''), rejected_quantity: '0', quality_grade: 'GRADE_A', rejection_reason: '' });
      setActiveView('procure');
      loadData(selectedCentreId!);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const skipToken = async (tokenId: number) => {
    try { await queueApi.skip(tokenId); loadData(selectedCentreId!); } catch (err: any) { setError(err.message); }
  };
  const noShow = async (tokenId: number) => {
    try { await queueApi.noShow(tokenId); loadData(selectedCentreId!); } catch (err: any) { setError(err.message); }
  };

  const submitProcurement = async () => {
    if (!processingToken) return;
    setProcureSubmitting(true);
    setError('');
    try {
      // Create procurement record
      const proc = await procurementsApi.create({
        booking_id: processingToken.booking_id,
        actual_quantity: Number(procureForm.actual_quantity),
        accepted_quantity: Number(procureForm.accepted_quantity),
        rejected_quantity: Number(procureForm.rejected_quantity),
        quality_grade: procureForm.quality_grade,
        rejection_reason: procureForm.rejection_reason || undefined,
      });

      // Mark procurement complete
      const completed = await procurementsApi.update(proc.id, { status: 'COMPLETED' });

      // Process payment
      const pay = await paymentsApi.process(completed.payment?.id || proc.id);

      // Complete queue token
      await queueApi.complete(processingToken.id);

      setProcureResult({ proc: completed, payment: pay });
      loadData(selectedCentreId!);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setProcureSubmitting(false);
    }
  };

  if (loading || fetching) {
    return <div className="min-h-screen bg-gray-50 flex items-center justify-center"><div className="text-3xl animate-pulse">🏛️</div></div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top nav */}
      <nav className="bg-[#1e3a5f] text-white px-4 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">🏛️</span>
            <div>
              <h1 className="font-bold text-sm">KisanSetu AI — Officer Desk</h1>
              <p className="text-xs text-blue-300">{user?.name}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={selectedCentreId || ''}
              onChange={(e) => setSelectedCentreId(Number(e.target.value))}
              className="bg-white/10 text-white border border-white/20 rounded-lg px-3 py-1.5 text-sm"
            >
              {centres.map((c) => <option key={c.id} value={c.id} className="text-gray-900">{c.name}</option>)}
            </select>
            <button onClick={() => { logout(); router.push('/'); }} className="text-xs text-blue-300 hover:text-white">Logout</button>
          </div>
        </div>
      </nav>

      {/* Tab navigation */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto flex">
          {(['dashboard', 'queue', 'procure'] as const).map((v) => (
            <button
              key={v}
              onClick={() => setActiveView(v)}
              className={`px-6 py-3 text-sm font-medium transition-colors capitalize ${activeView === v ? 'border-b-2 border-blue-700 text-blue-700' : 'text-gray-600 hover:text-gray-900'}`}
            >
              {v === 'dashboard' ? '📊 Dashboard' : v === 'queue' ? '📡 Live Queue' : '⚖️ Procure'}
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        {error && <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm mb-4">⚠️ {error}</div>}

        {/* DASHBOARD VIEW */}
        {activeView === 'dashboard' && dashboard && (
          <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
              {[
                { label: 'Expected Today', value: dashboard.expected_today, color: 'bg-blue-50 text-blue-700' },
                { label: 'Currently Processing', value: dashboard.currently_processing, color: 'bg-purple-50 text-purple-700' },
                { label: 'Waiting', value: dashboard.waiting, color: 'bg-amber-50 text-amber-700' },
                { label: 'Completed', value: dashboard.completed, color: 'bg-green-50 text-green-700' },
                { label: 'No Shows', value: dashboard.no_shows, color: 'bg-red-50 text-red-700' },
              ].map((s) => (
                <div key={s.label} className={`rounded-2xl p-4 ${s.color}`}>
                  <p className="text-xs font-medium opacity-75">{s.label}</p>
                  <p className="text-3xl font-extrabold mt-1">{s.value}</p>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-2xl p-4 border border-gray-200">
                <p className="text-xs text-gray-500">Avg Processing Time</p>
                <p className="text-2xl font-bold">{dashboard.avg_processing_minutes} min</p>
              </div>
              <div className="bg-white rounded-2xl p-4 border border-gray-200">
                <p className="text-xs text-gray-500">Congestion Score</p>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div className={`h-2 rounded-full ${dashboard.congestion_score < 25 ? 'bg-green-500' : dashboard.congestion_score < 50 ? 'bg-amber-500' : dashboard.congestion_score < 75 ? 'bg-orange-500' : 'bg-red-600'}`} style={{ width: `${dashboard.congestion_score}%` }} />
                  </div>
                  <span className="text-sm font-bold">{dashboard.congestion_score.toFixed(0)}/100</span>
                </div>
              </div>
            </div>

            {/* Call Next */}
            <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 text-center">
              <h3 className="font-bold text-gray-900 mb-2">Queue Control</h3>
              <p className="text-sm text-gray-500 mb-4">{dashboard.waiting} farmers waiting</p>
              <button
                onClick={callNext}
                disabled={dashboard.waiting === 0}
                className="bg-blue-700 text-white px-10 py-4 rounded-2xl text-lg font-bold hover:bg-blue-800 transition-colors disabled:opacity-40 shadow-lg"
              >
                📢 Call Next Farmer
              </button>
            </div>
          </div>
        )}

        {/* QUEUE VIEW */}
        {activeView === 'queue' && queue && (
          <div className="space-y-4">
            <div className="bg-white rounded-2xl p-4 border border-gray-200 flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Currently Processing</p>
                <p className="text-3xl font-extrabold font-mono text-green-800">{queue.current_token || '—'}</p>
              </div>
              <button
                onClick={callNext}
                className="bg-blue-700 text-white px-6 py-3 rounded-xl font-bold hover:bg-blue-800"
              >
                📢 Call Next
              </button>
            </div>

            <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
              <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 text-sm font-semibold text-gray-600">
                Waiting Queue ({queue.waiting_count} farmers)
              </div>
              {queue.queue?.length === 0 && (
                <div className="py-8 text-center text-gray-400">No farmers in queue</div>
              )}
              {queue.queue?.map((t: any) => (
                <div key={t.id} className="flex items-center justify-between px-4 py-3 border-b border-gray-100 last:border-0 hover:bg-gray-50">
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-lg w-14 text-green-800">{t.token_number}</span>
                    <div>
                      <p className="font-medium text-sm">{t.farmer_name || 'Farmer'}</p>
                      <p className="text-xs text-gray-400">{t.crop_name} — {t.expected_quantity} Qtl</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">~{t.estimated_wait_minutes} min</span>
                    <button onClick={() => startProcessing(t.id)} className="text-xs bg-green-700 text-white px-2 py-1 rounded-lg hover:bg-green-800">Start</button>
                    <button onClick={() => skipToken(t.id)} className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded-lg hover:bg-amber-200">Skip</button>
                    <button onClick={() => noShow(t.id)} className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-lg hover:bg-red-200">No Show</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* PROCUREMENT VIEW */}
        {activeView === 'procure' && (
          <div className="max-w-2xl mx-auto space-y-4">
            {procureResult ? (
              <div className="bg-white rounded-2xl p-8 border-2 border-green-400 text-center">
                <div className="text-5xl mb-4">✅</div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Procurement Complete!</h2>
                <div className="bg-green-50 rounded-2xl p-5 text-left mt-4 space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-gray-500">Receipt</span><span className="font-bold">{procureResult.proc.receipt_number}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Accepted Qty</span><span className="font-bold">{procureResult.proc.accepted_quantity} Qtl</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Grade</span><span className="font-bold">{procureResult.proc.quality_grade?.replace('_', ' ')}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">MSP Amount</span><span className="font-bold text-green-700 text-lg">₹{(procureResult.proc.procurement_amount || 0).toLocaleString('en-IN')}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Payment</span><span className="font-bold text-green-700">{procureResult.payment?.status || 'PROCESSING'}</span></div>
                </div>
                <button onClick={() => { setProcureResult(null); setProcessingToken(null); setActiveView('queue'); }} className="mt-5 bg-blue-700 text-white px-8 py-3 rounded-xl font-bold hover:bg-blue-800">
                  Process Next Farmer →
                </button>
              </div>
            ) : (
              <div className="bg-white rounded-2xl p-6 border border-gray-200">
                {processingToken ? (
                  <>
                    <div className="flex items-center gap-3 mb-5 pb-4 border-b border-gray-100">
                      <span className="text-3xl font-bold font-mono text-green-800 bg-green-100 rounded-xl px-4 py-2">{processingToken.token_number}</span>
                      <div>
                        <p className="font-bold">{processingToken.farmer_name}</p>
                        <p className="text-sm text-gray-500">{processingToken.crop_name} — Expected: {processingToken.expected_quantity} Qtl</p>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Actual Quantity (Qtl)</label>
                          <input type="number" value={procureForm.actual_quantity} onChange={e => setProcureForm(f => ({ ...f, actual_quantity: e.target.value }))} className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Accepted Quantity (Qtl)</label>
                          <input type="number" value={procureForm.accepted_quantity} onChange={e => { const val = e.target.value; setProcureForm(f => ({ ...f, accepted_quantity: val, rejected_quantity: String(Math.max(0, Number(f.actual_quantity) - Number(val))) })); }} className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Rejected Quantity (Qtl)</label>
                          <input type="number" value={procureForm.rejected_quantity} readOnly className="w-full border rounded-lg px-3 py-2 text-sm bg-gray-50" />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Quality Grade</label>
                          <select value={procureForm.quality_grade} onChange={e => setProcureForm(f => ({ ...f, quality_grade: e.target.value }))} className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="GRADE_A">Grade A — Premium Quality</option>
                            <option value="STANDARD">Standard Quality</option>
                            <option value="BELOW_STANDARD">Below Standard</option>
                          </select>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Rejection Reason (if any)</label>
                        <input type="text" value={procureForm.rejection_reason} onChange={e => setProcureForm(f => ({ ...f, rejection_reason: e.target.value }))} placeholder="Excessive moisture, foreign matter, etc." className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                      </div>
                      <button
                        onClick={submitProcurement}
                        disabled={procureSubmitting || !procureForm.accepted_quantity}
                        className="w-full bg-green-700 text-white py-3 rounded-xl font-bold text-lg hover:bg-green-800 disabled:opacity-50"
                      >
                        {procureSubmitting ? '⚖️ Processing...' : '✅ Complete Procurement & Process Payment'}
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-400">No active procurement. Go to Queue and start processing a token.</p>
                    <button onClick={() => setActiveView('queue')} className="mt-4 bg-blue-700 text-white px-5 py-2 rounded-lg text-sm">Go to Queue →</button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
