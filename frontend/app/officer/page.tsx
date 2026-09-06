'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/auth-context';
import { useWebSocket } from '@/context/websocket-context';
import { analyticsApi, queueApi, procurementsApi, paymentsApi, centresApi } from '@/lib/api';
import TokenCallModal, { CalledTokenData } from '@/components/TokenCallModal';
import ProcurementReceiptModal from '@/components/ProcurementReceiptModal';

export default function OfficerDashboard() {
  const { user, logout, loading } = useAuth();
  const { lastMessage, connectToQueue } = useWebSocket();
  const router = useRouter();

  const [centres, setCentres] = useState<any[]>([]);
  const [selectedCentreId, setSelectedCentreId] = useState<number | null>(null);
  const [dashboard, setDashboard] = useState<any>(null);
  const [queue, setQueue] = useState<any>(null);
  const [activeView, setActiveView] = useState<'dashboard' | 'queue' | 'procure' | 'records'>('dashboard');
  const [processingToken, setProcessingToken] = useState<any>(null);
  const [procureForm, setProcureForm] = useState({
    actual_quantity: '',
    accepted_quantity: '',
    rejected_quantity: '0',
    quality_grade: 'GRADE_A',
    rejection_reason: '',
  });
  const [procureSubmitting, setProcureSubmitting] = useState(false);
  const [procureResult, setProcureResult] = useState<any>(null);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');

  // Procurement Records State
  const [procurementRecords, setProcurementRecords] = useState<any[]>([]);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [selectedReceipt, setSelectedReceipt] = useState<any>(null);
  const [recordsSearch, setRecordsSearch] = useState('');
  const [recordsFilterGrade, setRecordsFilterGrade] = useState('ALL');
  const [recordsFilterCrop, setRecordsFilterCrop] = useState('ALL');

  // Token Call Modal State
  const [calledToken, setCalledToken] = useState<CalledTokenData | null>(null);
  const [isCallModalOpen, setIsCallModalOpen] = useState(false);
  const [isBatchAdding, setIsBatchAdding] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.push('/login');
    if (!loading && user && user.role === 'FARMER') router.push('/farmer');
  }, [user, loading, router]);

  useEffect(() => {
    centresApi
      .list()
      .then((cs) => {
        setCentres(cs);
        if (cs.length > 0) setSelectedCentreId(cs[0].id);
      })
      .catch(console.error);
  }, []);

  const loadProcurementRecords = useCallback(async (cId: number) => {
    setLoadingRecords(true);
    try {
      const recs = await procurementsApi.list(cId);
      setProcurementRecords(recs || []);
    } catch (err) {
      console.error('Failed to load procurement records:', err);
    } finally {
      setLoadingRecords(false);
    }
  }, []);

  const loadData = useCallback(async (cId: number) => {
    try {
      const [dash, q, recs] = await Promise.all([
        analyticsApi.officerDashboard(cId),
        queueApi.status(cId),
        procurementsApi.list(cId).catch(() => []),
      ]);
      setDashboard(dash);
      setQueue(q);
      if (recs && Array.isArray(recs)) {
        setProcurementRecords(recs);
      }

      // Auto-sync processing token from backend active_token if available
      if (q?.active_token) {
        setProcessingToken((prev: any) => {
          if (!prev || prev.id !== q.active_token.id) {
            setProcureForm({
              actual_quantity: String(q.active_token.expected_quantity || ''),
              accepted_quantity: String(q.active_token.expected_quantity || ''),
              rejected_quantity: '0',
              quality_grade: 'GRADE_A',
              rejection_reason: '',
            });
            return q.active_token;
          }
          return prev;
        });
      }
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
  }, [selectedCentreId, connectToQueue, loadData]);

  // Real-time updates via WebSocket
  useEffect(() => {
    if (lastMessage?.event === 'QUEUE_UPDATED' && selectedCentreId) {
      loadData(selectedCentreId);
    }
  }, [lastMessage, selectedCentreId, loadData]);

  // Polling fallback when WebSocket is not available (Vercel)
  useEffect(() => {
    if (!selectedCentreId) return;
    if (lastMessage !== null) return;
    const interval = setInterval(() => loadData(selectedCentreId), 8000);
    return () => clearInterval(interval);
  }, [selectedCentreId, lastMessage, loadData]);

  const callNext = async () => {
    if (!selectedCentreId) return;
    if (queue && queue.waiting_count === 0) {
      return;
    }
    setError('');
    try {
      const token = await queueApi.callNext(selectedCentreId);
      const centreName = centres.find((c) => c.id === selectedCentreId)?.name;
      setCalledToken({
        id: token.id,
        token_number: token.token_number,
        farmer_name: token.farmer_name,
        crop_name: token.crop_name,
        expected_quantity: token.expected_quantity,
        centre_name: centreName,
        booking_id: token.booking_id,
      });
      setIsCallModalOpen(true);
      loadData(selectedCentreId);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const startProcessing = async (tokenId: number, tokenData?: any) => {
    setError('');
    try {
      await queueApi.start(tokenId);
      const tok = tokenData || queue?.queue?.find((t: any) => t.id === tokenId);
      setProcessingToken(tok);
      setProcureForm({
        actual_quantity: String(tok?.expected_quantity || ''),
        accepted_quantity: String(tok?.expected_quantity || ''),
        rejected_quantity: '0',
        quality_grade: 'GRADE_A',
        rejection_reason: '',
      });
      setIsCallModalOpen(false);
      setActiveView('procure');
      loadData(selectedCentreId!);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const skipToken = async (tokenId: number) => {
    setError('');
    try {
      await queueApi.skip(tokenId);
      setProcessingToken(null);
      loadData(selectedCentreId!);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const noShow = async (tokenId: number) => {
    setError('');
    try {
      await queueApi.noShow(tokenId);
      setProcessingToken(null);
      loadData(selectedCentreId!);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddFarmers = async () => {
    if (!selectedCentreId || isBatchAdding) return;
    setError('');
    setIsBatchAdding(true);
    try {
      await queueApi.addFarmers(selectedCentreId, 10);
      await loadData(selectedCentreId);
    } catch (err: any) {
      setError(err.message || 'Failed to check-in farmers');
    } finally {
      setIsBatchAdding(false);
    }
  };

  const handleResetQueue = async () => {
    if (!selectedCentreId || isResetting) return;
    setError('');
    setIsResetting(true);
    try {
      await queueApi.reset(selectedCentreId);
      setProcessingToken(null);
      await loadData(selectedCentreId);
    } catch (err: any) {
      setError(err.message || 'Failed to reset queue');
    } finally {
      setIsResetting(false);
    }
  };

  const submitProcurement = async () => {
    const tok = processingToken || queue?.active_token;
    if (!tok) return;
    setProcureSubmitting(true);
    setError('');
    try {
      const proc = await procurementsApi.create({
        booking_id: tok.booking_id,
        actual_quantity: Number(procureForm.actual_quantity || tok.expected_quantity),
        accepted_quantity: Number(procureForm.accepted_quantity || tok.expected_quantity),
        rejected_quantity: Number(procureForm.rejected_quantity || 0),
        quality_grade: procureForm.quality_grade,
        rejection_reason: procureForm.rejection_reason || undefined,
      });

      const completed = await procurementsApi.update(proc.id, { status: 'COMPLETED' });
      const pay = await paymentsApi.process(completed.payment?.id || proc.id);
      try {
        await queueApi.complete(tok.id);
      } catch (qErr: any) {
        console.warn('Queue complete notice:', qErr);
      }

      setProcureResult({ proc: completed, payment: pay });
      setProcessingToken(null);
      if (selectedCentreId) await loadData(selectedCentreId);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setProcureSubmitting(false);
    }
  };

  const activeServingToken = processingToken || queue?.active_token || null;
  const alreadyProcuredRecord = activeServingToken
    ? procurementRecords.find(
        (p: any) =>
          p.booking_id === activeServingToken.booking_id ||
          (activeServingToken.farmer_name && p.farmer_name === activeServingToken.farmer_name)
      )
    : null;

  const filteredRecords = procurementRecords.filter((r: any) => {
    if (recordsFilterGrade !== 'ALL' && r.quality_grade !== recordsFilterGrade) return false;
    if (recordsFilterCrop !== 'ALL' && r.crop_name !== recordsFilterCrop) return false;
    if (recordsSearch.trim()) {
      const q = recordsSearch.toLowerCase();
      const matchName = r.farmer_name?.toLowerCase().includes(q);
      const matchReceipt = r.receipt_number?.toLowerCase().includes(q);
      const matchCrop = r.crop_name?.toLowerCase().includes(q);
      const matchBooking = r.booking_number?.toLowerCase().includes(q);
      return Boolean(matchName || matchReceipt || matchCrop || matchBooking);
    }
    return true;
  });

  if (loading || fetching) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-3xl animate-pulse">🏛️</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Clean In-Theme Token Call Modal */}
      <TokenCallModal
        token={calledToken}
        isOpen={isCallModalOpen}
        onClose={() => setIsCallModalOpen(false)}
        onStartProcure={(tok) => startProcessing(tok.id, tok)}
      />

      {/* Top nav */}
      <nav className="bg-[#1e3a5f] text-white px-4 py-3">
        <div className="w-full max-w-[1600px] mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">🏛️</span>
            <div>
              <h1 className="font-bold text-sm">KisanSetu AI — Officer Desk</h1>
              <p className="text-xs text-blue-300">{user?.name}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setError('');
                setActiveView('records');
                if (selectedCentreId) loadProcurementRecords(selectedCentreId);
              }}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-colors cursor-pointer flex items-center gap-1.5 ${
                activeView === 'records'
                  ? 'bg-blue-600 text-white border-blue-400 font-bold shadow-xs'
                  : 'bg-white/10 hover:bg-white/20 text-white border-white/20'
              }`}
              title="View all Mandi procurement records"
            >
              <span>📜</span>
              <span className="hidden sm:inline">Procurement Records</span>
              <span className="sm:hidden">Records</span>
              {procurementRecords.length > 0 && (
                <span className="bg-white/20 text-white text-2xs px-1.5 py-0.2 rounded-full font-mono font-bold">
                  {procurementRecords.length}
                </span>
              )}
            </button>
            <select
              value={selectedCentreId || ''}
              onChange={(e) => setSelectedCentreId(Number(e.target.value))}
              className="bg-white/10 text-white border border-white/20 rounded-lg px-3 py-1.5 text-sm"
            >
              {centres.map((c) => (
                <option key={c.id} value={c.id} className="text-gray-900">
                  {c.name}
                </option>
              ))}
            </select>
            <button
              onClick={() => {
                logout();
                router.push('/');
              }}
              className="text-xs text-blue-300 hover:text-white cursor-pointer"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Tab navigation */}
      <div className="bg-white border-b">
        <div className="w-full max-w-[1600px] mx-auto flex items-center justify-between px-4">
          <div className="flex overflow-x-auto">
            {(['dashboard', 'queue', 'procure', 'records'] as const).map((v) => (
              <button
                key={v}
                onClick={() => {
                  setError('');
                  setActiveView(v);
                  if (v === 'records' && selectedCentreId) {
                    loadProcurementRecords(selectedCentreId);
                  }
                }}
                className={`px-5 sm:px-6 py-3 text-sm font-medium transition-colors cursor-pointer flex items-center gap-2 whitespace-nowrap ${
                  activeView === v
                    ? 'border-b-2 border-blue-700 text-blue-700 font-bold'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <span>
                  {v === 'dashboard'
                    ? '📊 Dashboard'
                    : v === 'queue'
                    ? '📡 Live Queue'
                    : v === 'procure'
                    ? '⚖️ Procure'
                    : '📜 Procurement Records'}
                </span>
                {v === 'records' && procurementRecords.length > 0 && (
                  <span className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full font-mono font-bold">
                    {procurementRecords.length}
                  </span>
                )}
              </button>
            ))}
          </div>
          <div className="hidden md:flex items-center gap-2">
            <button
              onClick={() => {
                setError('');
                setActiveView('records');
                if (selectedCentreId) loadProcurementRecords(selectedCentreId);
              }}
              className="text-xs font-bold text-blue-700 hover:text-blue-900 bg-blue-50 hover:bg-blue-100 border border-blue-200 px-3.5 py-1.5 rounded-xl transition-colors cursor-pointer flex items-center gap-1.5 shadow-2xs"
            >
              <span>📋</span>
              <span>All Mandi Records ({procurementRecords.length})</span>
            </button>
          </div>
        </div>
      </div>

      <div className="w-full max-w-[1600px] mx-auto px-4 py-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm mb-4 flex flex-wrap items-center justify-between gap-3 shadow-xs">
            <div className="flex items-center gap-2">
              <span className="text-base">⚠️</span>
              <span className="font-medium">{error}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  setError('');
                  setActiveView('records');
                  if (selectedCentreId) loadProcurementRecords(selectedCentreId);
                }}
                className="bg-red-700 hover:bg-red-800 text-white text-xs font-bold px-3.5 py-1.5 rounded-lg shadow-xs transition-colors cursor-pointer flex items-center gap-1"
              >
                <span>📜 View in Procurement Records →</span>
              </button>
              <button
                onClick={() => setError('')}
                className="text-red-400 hover:text-red-700 text-xs font-bold px-1.5 py-0.5 rounded cursor-pointer"
              >
                ✕
              </button>
            </div>
          </div>
        )}

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
                <p className="text-xs text-slate-500 font-medium">Avg Processing Time</p>
                <p className="text-2xl font-bold text-slate-900">{dashboard.avg_processing_minutes} min</p>
              </div>
              <div className="bg-white rounded-2xl p-4 border border-gray-200">
                <p className="text-xs text-slate-500 font-medium">Congestion Score</p>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        dashboard.congestion_score < 25
                          ? 'bg-green-500'
                          : dashboard.congestion_score < 50
                          ? 'bg-amber-500'
                          : dashboard.congestion_score < 75
                          ? 'bg-orange-500'
                          : 'bg-red-600'
                      }`}
                      style={{ width: `${dashboard.congestion_score}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold text-slate-900">
                    {dashboard.congestion_score.toFixed(0)}/100
                  </span>
                </div>
              </div>
            </div>

            {/* Queue Control */}
            <div className="bg-white rounded-2xl p-6 border-2 border-blue-200 text-center">
              <h3 className="font-bold text-gray-900 mb-2">Queue Control</h3>
              <p className="text-sm text-gray-500 mb-4">{dashboard.waiting} farmers waiting</p>
              <div className="flex flex-wrap items-center justify-center gap-3">
                <button
                  onClick={callNext}
                  disabled={dashboard.waiting === 0}
                  className="bg-blue-700 text-white px-8 py-3.5 rounded-2xl text-base font-bold hover:bg-blue-800 transition-colors disabled:opacity-40 shadow-md cursor-pointer"
                >
                  📢 Call Next Farmer
                </button>
                {dashboard.waiting === 0 && (
                  <button
                    onClick={handleAddFarmers}
                    disabled={isBatchAdding}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-3.5 rounded-2xl text-base font-bold transition-colors shadow-md cursor-pointer disabled:opacity-50 flex items-center gap-2"
                  >
                    <span>➕</span>
                    <span>{isBatchAdding ? 'Checking In...' : 'Check-in Next 10 Farmers'}</span>
                  </button>
                )}
                <button
                  onClick={handleResetQueue}
                  disabled={isResetting}
                  className="bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300 px-5 py-3.5 rounded-2xl text-sm font-semibold transition-colors cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                  title="Reset demo queue"
                >
                  <span>🔄</span>
                  <span>{isResetting ? 'Resetting...' : 'Reset Queue'}</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* QUEUE VIEW */}
        {activeView === 'queue' && queue && (
          <div className="space-y-4">
            {/* Active Serving Card */}
            <div className={`bg-white rounded-2xl p-5 border-2 shadow-xs transition-all ${activeServingToken ? 'border-green-300 bg-gradient-to-r from-green-50/30 to-white' : 'border-gray-200'}`}>
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className={`font-mono text-4xl font-black px-4 py-2.5 rounded-2xl border ${
                    activeServingToken || queue.current_token
                      ? 'bg-green-100 text-green-900 border-green-300 shadow-xs'
                      : 'bg-gray-100 text-gray-400 border-gray-200'
                  }`}>
                    {queue.current_token || activeServingToken?.token_number || '—'}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500 font-semibold uppercase tracking-wider">
                        Currently Serving
                      </span>
                      {activeServingToken && (
                        <span className={`text-2xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                          activeServingToken.status === 'CALLED'
                            ? 'bg-blue-100 text-blue-800 border border-blue-200'
                            : 'bg-purple-100 text-purple-800 border border-purple-200'
                        }`}>
                          {activeServingToken.status === 'CALLED' ? '📢 Called' : '⚖️ Processing'}
                        </span>
                      )}
                    </div>
                    <p className="font-bold text-gray-900 text-base mt-0.5">
                      {activeServingToken?.farmer_name || (queue.current_token ? 'Farmer' : 'Counter Idle')}
                    </p>
                    <p className="text-xs text-gray-500">
                      {activeServingToken?.crop_name
                        ? `${activeServingToken.crop_name}${activeServingToken.expected_quantity ? ` — ${activeServingToken.expected_quantity} Qtl expected` : ''}`
                        : queue.current_token
                        ? 'Inspection and weighing at Counter 1'
                        : 'No active farmer at the counter'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-wrap md:flex-nowrap">
                  {/* Action 1: Procure Produce */}
                  {activeServingToken && (
                    <button
                      onClick={() => startProcessing(activeServingToken.id, activeServingToken)}
                      className="bg-green-700 hover:bg-green-800 text-white px-5 py-2.5 rounded-xl font-bold text-sm shadow-xs flex items-center gap-1.5 cursor-pointer transition-colors"
                    >
                      <span>⚖️ Procure Produce →</span>
                    </button>
                  )}

                  {/* Action 2: Skip / No Show */}
                  {activeServingToken && (
                    <>
                      <button
                        onClick={() => skipToken(activeServingToken.id)}
                        className="bg-amber-100 hover:bg-amber-200 text-amber-800 px-3 py-2.5 rounded-xl text-xs font-semibold cursor-pointer transition-colors"
                        title="Skip this token"
                      >
                        Skip
                      </button>
                      <button
                        onClick={() => noShow(activeServingToken.id)}
                        className="bg-red-100 hover:bg-red-200 text-red-800 px-3 py-2.5 rounded-xl text-xs font-semibold cursor-pointer transition-colors"
                        title="Mark as No Show"
                      >
                        No Show
                      </button>
                    </>
                  )}

                  {/* Action 3: Call Next Button */}
                  <button
                    onClick={callNext}
                    disabled={queue.waiting_count === 0}
                    className={`px-5 py-2.5 rounded-xl font-bold text-sm flex items-center gap-2 transition-colors ${
                      queue.waiting_count === 0
                        ? 'bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed'
                        : 'bg-blue-700 hover:bg-blue-800 text-white shadow-xs cursor-pointer'
                    }`}
                    title={queue.waiting_count === 0 ? 'No farmers waiting in queue' : 'Call next farmer from queue'}
                  >
                    <span>📢 Call Next</span>
                    {queue.waiting_count > 0 && (
                      <span className="bg-blue-900 text-blue-200 text-xs px-2 py-0.5 rounded-full font-mono">
                        {queue.waiting_count}
                      </span>
                    )}
                  </button>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
              <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 text-sm font-semibold text-gray-600 flex items-center justify-between">
                <span>Waiting Queue ({queue.waiting_count} farmers)</span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleAddFarmers}
                    disabled={isBatchAdding}
                    className="text-xs bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 px-3 py-1.5 rounded-lg font-semibold flex items-center gap-1.5 transition-colors cursor-pointer disabled:opacity-50"
                    title="Check-in next batch of farmers from confirmed bookings"
                  >
                    <span>➕</span>
                    <span>{isBatchAdding ? 'Checking In...' : 'Check-in Farmers'}</span>
                  </button>
                  <button
                    onClick={handleResetQueue}
                    disabled={isResetting}
                    className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 border border-gray-200 px-2.5 py-1.5 rounded-lg font-medium flex items-center gap-1 transition-colors cursor-pointer disabled:opacity-50"
                    title="Reset queue tokens to initial state"
                  >
                    <span>🔄</span>
                    <span>{isResetting ? 'Resetting...' : 'Reset'}</span>
                  </button>
                </div>
              </div>
              {(!queue.queue || queue.queue.length === 0) && (
                <div className="py-12 px-4 text-center text-gray-400">
                  <p className="text-3xl mb-2">🌾</p>
                  <p className="text-base font-bold text-gray-700">No farmers waiting in queue</p>
                  <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
                    All currently arrived farmers have been served or called. Check-in the next scheduled batch of booked farmers to continue operations.
                  </p>
                  <div className="mt-5 flex items-center justify-center gap-3">
                    <button
                      onClick={handleAddFarmers}
                      disabled={isBatchAdding}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold px-5 py-2.5 rounded-xl shadow-xs transition-colors cursor-pointer disabled:opacity-50 flex items-center gap-2"
                    >
                      <span>➕</span>
                      <span>{isBatchAdding ? 'Checking in...' : 'Check-in Next 10 Farmers'}</span>
                    </button>
                    <button
                      onClick={handleResetQueue}
                      disabled={isResetting}
                      className="bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-200 text-sm font-medium px-4 py-2.5 rounded-xl transition-colors cursor-pointer disabled:opacity-50"
                    >
                      {isResetting ? 'Resetting...' : '🔄 Reset Live Queue'}
                    </button>
                  </div>
                </div>
              )}
              {queue.queue?.map((t: any) => (
                <div
                  key={t.id}
                  className="flex items-center justify-between px-4 py-3 border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-lg w-14 text-green-800">{t.token_number}</span>
                    <div>
                      <p className="font-semibold text-sm text-slate-900">{t.farmer_name || 'Farmer'}</p>
                      <p className="text-xs text-slate-500">
                        {t.crop_name} — {t.expected_quantity} Qtl
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500 font-medium">~{t.estimated_wait_minutes} min</span>
                    <button
                      onClick={() => startProcessing(t.id, t)}
                      className="text-xs bg-green-700 text-white px-2.5 py-1.5 rounded-lg hover:bg-green-800 cursor-pointer font-medium"
                    >
                      Start
                    </button>
                    <button
                      onClick={() => skipToken(t.id)}
                      className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded-lg hover:bg-amber-200 cursor-pointer"
                    >
                      Skip
                    </button>
                    <button
                      onClick={() => noShow(t.id)}
                      className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-lg hover:bg-red-200 cursor-pointer"
                    >
                      No Show
                    </button>
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
              <div className="bg-white rounded-2xl p-8 border-2 border-green-400 text-center shadow-md">
                <div className="text-5xl mb-4">✅</div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Procurement Complete!</h2>
                <div className="bg-green-50 rounded-2xl p-5 text-left mt-4 space-y-2 text-sm border border-green-200">
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-medium">Receipt</span>
                    <span className="font-bold text-slate-900">{procureResult.proc.receipt_number}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-medium">Accepted Qty</span>
                    <span className="font-bold text-slate-900">{procureResult.proc.accepted_quantity} Qtl</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-medium">Grade</span>
                    <span className="font-bold text-slate-900">{procureResult.proc.quality_grade?.replace('_', ' ')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-medium">MSP Amount</span>
                    <span className="font-bold text-green-700 text-lg">
                      ₹{(procureResult.proc.procurement_amount || 0).toLocaleString('en-IN')}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-medium">Payment</span>
                    <span className="font-bold text-green-700">{procureResult.payment?.status || 'PROCESSING'}</span>
                  </div>
                </div>
                <div className="flex flex-wrap items-center justify-center gap-3 mt-5">
                  <button
                    onClick={async () => {
                      setProcureResult(null);
                      setProcessingToken(null);
                      if (selectedCentreId && queue.waiting_count > 0) {
                        try {
                          await queueApi.callNext(selectedCentreId);
                        } catch {}
                      }
                      setActiveView('queue');
                      if (selectedCentreId) await loadData(selectedCentreId);
                    }}
                    className="bg-blue-700 text-white px-6 py-3 rounded-xl font-bold hover:bg-blue-800 cursor-pointer shadow-md text-sm"
                  >
                    Process Next Farmer →
                  </button>
                  <button
                    onClick={() => {
                      setSelectedReceipt(procureResult.proc);
                    }}
                    className="bg-emerald-700 text-white px-5 py-3 rounded-xl font-bold hover:bg-emerald-800 cursor-pointer shadow-md text-sm flex items-center gap-1.5"
                  >
                    <span>📜</span>
                    <span>View Digital Receipt</span>
                  </button>
                  <button
                    onClick={() => {
                      setActiveView('records');
                    }}
                    className="bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300 px-5 py-3 rounded-xl font-semibold cursor-pointer text-sm"
                  >
                    All Records
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-xs">
                {activeServingToken ? (
                  <>
                    {alreadyProcuredRecord && (
                      <div className="bg-amber-50 border-2 border-amber-200 rounded-2xl p-4 mb-5 text-xs text-amber-900 shadow-xs">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                          <div className="flex items-center gap-2.5">
                            <span className="text-2xl">⚠️</span>
                            <div>
                              <p className="font-bold text-sm text-amber-950">
                                Procurement Record Already Exists For This Booking
                              </p>
                              <p className="text-amber-800 mt-0.5">
                                Produce has already been graded and recorded (Receipt:{' '}
                                <strong className="font-mono">{alreadyProcuredRecord.receipt_number}</strong>, Amount:{' '}
                                <strong>₹{(alreadyProcuredRecord.procurement_amount || 0).toLocaleString('en-IN')}</strong>).
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <button
                              type="button"
                              onClick={() => setSelectedReceipt(alreadyProcuredRecord)}
                              className="bg-amber-700 hover:bg-amber-800 text-white text-xs font-bold px-3.5 py-2 rounded-xl transition-colors cursor-pointer flex items-center gap-1 shadow-xs"
                            >
                              <span>📜 View Receipt</span>
                            </button>
                            <button
                              type="button"
                              onClick={async () => {
                                const tokenToComplete = activeServingToken;
                                setProcessingToken(null);
                                setError('');
                                if (tokenToComplete?.id) {
                                  try {
                                    await queueApi.complete(tokenToComplete.id);
                                  } catch (e: any) {
                                    if (tokenToComplete.booking_id) {
                                      try {
                                        await queueApi.complete(tokenToComplete.booking_id);
                                      } catch {}
                                    }
                                  }
                                }
                                if (selectedCentreId) {
                                  if (queue?.waiting_count > 0) {
                                    try {
                                      await queueApi.callNext(selectedCentreId);
                                    } catch {}
                                  }
                                  await loadData(selectedCentreId);
                                }
                                setActiveView('queue');
                              }}
                              className="bg-white hover:bg-amber-100 text-amber-900 border border-amber-300 text-xs font-bold px-3.5 py-2 rounded-xl transition-colors cursor-pointer shadow-2xs"
                            >
                              Mark Complete & Next →
                            </button>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="flex items-center gap-4 mb-5 pb-4 border-b border-gray-100">
                      <span className="text-3xl font-bold font-mono text-green-800 bg-green-100 rounded-xl px-4 py-2 border border-green-200">
                        {activeServingToken.token_number}
                      </span>
                      <div>
                        <p className="font-bold text-lg text-gray-900">{activeServingToken.farmer_name || 'Farmer'}</p>
                        <p className="text-sm text-gray-500">
                          {activeServingToken.crop_name} — Expected: {activeServingToken.expected_quantity} Qtl
                        </p>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Actual Quantity (Qtl)</label>
                          <input
                            type="number"
                            value={procureForm.actual_quantity}
                            onChange={(e) => setProcureForm((f) => ({ ...f, actual_quantity: e.target.value }))}
                            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Accepted Quantity (Qtl)</label>
                          <input
                            type="number"
                            value={procureForm.accepted_quantity}
                            onChange={(e) => {
                              const val = e.target.value;
                              setProcureForm((f) => ({
                                ...f,
                                accepted_quantity: val,
                                rejected_quantity: String(Math.max(0, Number(f.actual_quantity) - Number(val))),
                              }));
                            }}
                            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Rejected Quantity (Qtl)</label>
                          <input
                            type="number"
                            value={procureForm.rejected_quantity}
                            readOnly
                            className="w-full border rounded-lg px-3 py-2 text-sm bg-gray-50"
                          />
                        </div>
                        <div className="col-span-2">
                          <label className="block text-sm font-medium text-gray-700 mb-1.5">Quality Inspection Grade</label>
                          <div className="grid grid-cols-3 gap-2.5">
                            {[
                              { value: 'GRADE_A', label: 'Grade A', sub: 'FAQ Premium (100% MSP)', dot: 'bg-emerald-500', activeBg: 'bg-emerald-50 border-emerald-500 text-emerald-900 ring-2 ring-emerald-500/20' },
                              { value: 'STANDARD', label: 'Standard', sub: 'Standard Quality (95% MSP)', dot: 'bg-amber-500', activeBg: 'bg-amber-50 border-amber-500 text-amber-900 ring-2 ring-amber-500/20' },
                              { value: 'BELOW_STANDARD', label: 'Below Std', sub: 'Discounted (85% MSP)', dot: 'bg-rose-500', activeBg: 'bg-rose-50 border-rose-500 text-rose-900 ring-2 ring-rose-500/20' },
                            ].map((g) => {
                              const isSelected = procureForm.quality_grade === g.value;
                              return (
                                <button
                                  type="button"
                                  key={g.value}
                                  onClick={() => setProcureForm((f) => ({ ...f, quality_grade: g.value }))}
                                  className={`px-3 py-2.5 rounded-xl text-center border transition-all cursor-pointer ${
                                    isSelected
                                      ? `${g.activeBg} font-bold shadow-xs`
                                      : 'border-gray-200 hover:bg-gray-50 text-gray-700 font-medium'
                                  }`}
                                >
                                  <div className="flex items-center justify-center gap-1.5 text-xs">
                                    <span className={`w-2 h-2 rounded-full ${g.dot} shrink-0`}></span>
                                    <span>{g.label}</span>
                                  </div>
                                  <div className="text-2xs opacity-75 font-normal mt-0.5">{g.sub}</div>
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Rejection Reason (if any)</label>
                        <input
                          type="text"
                          value={procureForm.rejection_reason}
                          onChange={(e) => setProcureForm((f) => ({ ...f, rejection_reason: e.target.value }))}
                          placeholder="Excessive moisture, foreign matter, etc."
                          className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <button
                        onClick={submitProcurement}
                        disabled={procureSubmitting || !procureForm.accepted_quantity}
                        className="w-full bg-green-700 text-white py-3.5 rounded-xl font-bold text-lg hover:bg-green-800 disabled:opacity-50 cursor-pointer shadow-md transition-colors"
                      >
                        {procureSubmitting ? '⚖️ Processing...' : '✅ Complete Procurement & Process Payment'}
                      </button>
                      <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                        <button
                          type="button"
                          onClick={() => {
                            setError('');
                            setActiveView('records');
                            if (selectedCentreId) loadProcurementRecords(selectedCentreId);
                          }}
                          className="text-xs text-blue-700 hover:text-blue-900 font-bold cursor-pointer flex items-center gap-1"
                        >
                          <span>📜 View All Procurement Records ({procurementRecords.length}) →</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setError('');
                            setProcessingToken(null);
                            setActiveView('queue');
                          }}
                          className="text-xs text-gray-500 hover:text-gray-700 cursor-pointer"
                        >
                          Return to Live Queue
                        </button>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-10">
                    <div className="text-4xl mb-3">⚖️</div>
                    <h3 className="text-lg font-bold text-gray-900 mb-1">No Active Procurement</h3>
                    <p className="text-gray-500 text-sm max-w-md mx-auto mb-5">
                      {queue?.waiting_count && queue.waiting_count > 0
                        ? `There are ${queue.waiting_count} farmer(s) waiting in queue. Go to Live Queue and call or start the next token to begin weighing and procurement.`
                        : 'All farmers have been served today. No tokens waiting in queue.'}
                    </p>
                    <div className="flex items-center justify-center gap-3">
                      <button
                        onClick={() => {
                          setError('');
                          setActiveView('queue');
                        }}
                        className="bg-blue-700 hover:bg-blue-800 text-white font-bold px-6 py-2.5 rounded-xl text-sm transition-colors cursor-pointer shadow-xs inline-flex items-center gap-2"
                      >
                        <span>Go to Live Queue →</span>
                      </button>
                      <button
                        onClick={() => {
                          setError('');
                          setActiveView('records');
                          if (selectedCentreId) loadProcurementRecords(selectedCentreId);
                        }}
                        className="bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300 font-bold px-5 py-2.5 rounded-xl text-sm transition-colors cursor-pointer shadow-2xs inline-flex items-center gap-1.5"
                      >
                        <span>📜 Procurement Records ({procurementRecords.length})</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* PROCUREMENT RECORDS VIEW */}
        {activeView === 'records' && (
          <div className="space-y-6">
            {/* Top Header & Search Bar */}
            <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-xs">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                    <span>📜</span>
                    <span>Mandi Procurement Register & J-Forms</span>
                  </h2>
                  <p className="text-xs text-gray-500 mt-1">
                    Official Fair Average Quality (FAQ) MSP purchase records and digital payment receipts.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => selectedCentreId && loadProcurementRecords(selectedCentreId)}
                    disabled={loadingRecords}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-200 text-xs font-semibold px-3.5 py-2 rounded-xl transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
                  >
                    <span className={loadingRecords ? 'animate-spin' : ''}>🔄</span>
                    <span>{loadingRecords ? 'Refreshing...' : 'Refresh Records'}</span>
                  </button>
                </div>
              </div>

              {/* Filters */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-5 pt-5 border-t border-gray-100">
                <div className="relative">
                  <input
                    type="text"
                    placeholder="🔍 Search Farmer, Receipt (RCP-...) or Crop..."
                    value={recordsSearch}
                    onChange={(e) => setRecordsSearch(e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {recordsSearch && (
                    <button
                      onClick={() => setRecordsSearch('')}
                      className="absolute right-3 top-2 text-gray-400 hover:text-gray-600 text-xs font-bold"
                    >
                      ✕
                    </button>
                  )}
                </div>

                <div>
                  <select
                    value={recordsFilterGrade}
                    onChange={(e) => setRecordsFilterGrade(e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="ALL">All Quality Grades</option>
                    <option value="GRADE_A">Grade A (FAQ Premium)</option>
                    <option value="STANDARD">Standard Grade</option>
                    <option value="BELOW_STANDARD">Below Standard</option>
                  </select>
                </div>

                <div>
                  <select
                    value={recordsFilterCrop}
                    onChange={(e) => setRecordsFilterCrop(e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="ALL">All Crops / Commodities</option>
                    {Array.from(new Set(procurementRecords.map((p: any) => p.crop_name).filter(Boolean))).map((crop) => (
                      <option key={crop} value={crop}>
                        {crop}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* KPI Stat Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-white rounded-2xl p-4 border border-gray-200 shadow-2xs">
                <p className="text-xs text-gray-500 font-medium">Total Transactions</p>
                <p className="text-2xl font-black text-gray-900 mt-1 font-mono">
                  {procurementRecords.length}
                </p>
                <p className="text-2xs text-gray-400 mt-0.5">Procured farmers</p>
              </div>

              <div className="bg-white rounded-2xl p-4 border border-gray-200 shadow-2xs">
                <p className="text-xs text-gray-500 font-medium">Total Volume Procured</p>
                <p className="text-2xl font-black text-blue-700 mt-1 font-mono">
                  {procurementRecords.reduce((acc: number, p: any) => acc + Number(p.accepted_quantity || 0), 0).toFixed(1)} <span className="text-xs font-normal">Qtl</span>
                </p>
                <p className="text-2xs text-gray-400 mt-0.5">Accepted weight</p>
              </div>

              <div className="bg-white rounded-2xl p-4 border border-gray-200 shadow-2xs">
                <p className="text-xs text-gray-500 font-medium">Total MSP Disbursed</p>
                <p className="text-2xl font-black text-emerald-700 mt-1 font-mono">
                  ₹{Math.round(procurementRecords.reduce((acc: number, p: any) => acc + Number(p.procurement_amount || 0), 0)).toLocaleString('en-IN')}
                </p>
                <p className="text-2xs text-gray-400 mt-0.5">Government MSP payout</p>
              </div>

              <div className="bg-white rounded-2xl p-4 border border-gray-200 shadow-2xs">
                <p className="text-xs text-gray-500 font-medium">Grade A Pass Rate</p>
                <p className="text-2xl font-black text-purple-700 mt-1 font-mono">
                  {procurementRecords.length > 0
                    ? `${Math.round((procurementRecords.filter((p: any) => p.quality_grade === 'GRADE_A').length / procurementRecords.length) * 100)}%`
                    : '—'}
                </p>
                <p className="text-2xs text-gray-400 mt-0.5">FAQ Premium produce</p>
              </div>
            </div>

            {/* Records List / Table */}
            <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-xs">
              <div className="px-5 py-3.5 bg-gray-50 border-b border-gray-200 flex items-center justify-between text-xs font-bold text-gray-700">
                <span>
                  Showing {filteredRecords.length} of {procurementRecords.length} procurement records
                </span>
                {(recordsSearch || recordsFilterGrade !== 'ALL' || recordsFilterCrop !== 'ALL') && (
                  <button
                    onClick={() => {
                      setRecordsSearch('');
                      setRecordsFilterGrade('ALL');
                      setRecordsFilterCrop('ALL');
                    }}
                    className="text-blue-600 hover:text-blue-800 font-semibold cursor-pointer"
                  >
                    Reset Filters
                  </button>
                )}
              </div>

              {loadingRecords ? (
                <div className="py-16 text-center text-gray-400">
                  <div className="text-3xl animate-spin mb-2">🔄</div>
                  <p className="text-sm font-medium">Loading procurement records...</p>
                </div>
              ) : filteredRecords.length === 0 ? (
                <div className="py-16 px-4 text-center text-gray-400">
                  <p className="text-4xl mb-2">🌾</p>
                  <p className="text-base font-bold text-gray-700">No matching procurement records found</p>
                  <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
                    Try adjusting your search terms or filters above to find specific receipts.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-gray-200 bg-gray-50 text-gray-500 font-semibold uppercase tracking-wider text-2xs">
                        <th className="px-4 py-3 whitespace-nowrap">Receipt No / J-Form</th>
                        <th className="px-3.5 py-3 whitespace-nowrap">Farmer & Booking</th>
                        <th className="px-3.5 py-3 whitespace-nowrap">Crop / Produce</th>
                        <th className="px-3.5 py-3 text-right whitespace-nowrap">Accepted Qty</th>
                        <th className="px-3.5 py-3 text-center whitespace-nowrap">Grade</th>
                        <th className="px-3.5 py-3 text-right whitespace-nowrap">MSP Amount</th>
                        <th className="px-3.5 py-3 text-center whitespace-nowrap">Status</th>
                        <th className="px-4 py-3 text-right whitespace-nowrap">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {filteredRecords.map((r: any) => {
                        const dateStr = r.created_at
                          ? new Date(r.created_at).toLocaleDateString('en-IN', {
                              day: '2-digit',
                              month: 'short',
                              year: 'numeric',
                            })
                          : 'Recent';

                        return (
                          <tr key={r.id || r.receipt_number} className="hover:bg-blue-50/40 transition-colors">
                            <td className="px-4 py-3 whitespace-nowrap">
                              <button
                                onClick={() => setSelectedReceipt(r)}
                                className="font-mono font-bold text-blue-700 hover:text-blue-900 hover:underline cursor-pointer inline-flex items-center gap-1.5 whitespace-nowrap"
                                title="Click to view digital receipt"
                              >
                                <span>📜</span>
                                <span>{r.receipt_number || `RCP-KNL-2026-${String(r.id).padStart(5, '0')}`}</span>
                              </button>
                              <p className="text-2xs text-gray-400 mt-0.5">{dateStr}</p>
                            </td>
                            <td className="px-3.5 py-3 whitespace-nowrap">
                              <p className="font-bold text-gray-900">{r.farmer_name || 'Registered Farmer'}</p>
                              <p className="text-2xs text-gray-500 font-mono">
                                {r.booking_number || `BK-KNL-2026-${r.booking_id}`}
                              </p>
                            </td>
                            <td className="px-3.5 py-3 whitespace-nowrap">
                              <p className="font-semibold text-gray-900">{r.crop_name || 'Produce'}</p>
                              <p className="text-2xs text-gray-400">
                                {r.expected_quantity ? `Exp: ${r.expected_quantity} Qtl` : ''}
                              </p>
                            </td>
                            <td className="px-3.5 py-3 text-right font-mono whitespace-nowrap">
                              <span className="font-bold text-gray-900 text-sm">{r.accepted_quantity ?? '—'}</span>{' '}
                              <span className="text-gray-500 text-xs font-normal">Qtl</span>
                            </td>
                            <td className="px-3.5 py-3 text-center whitespace-nowrap">
                              {r.quality_grade === 'GRADE_A' ? (
                                <span className="whitespace-nowrap inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-300 shadow-2xs">
                                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0"></span>
                                  <span>Grade A</span>
                                </span>
                              ) : r.quality_grade === 'STANDARD' ? (
                                <span className="whitespace-nowrap inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-300 shadow-2xs">
                                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0"></span>
                                  <span>Standard</span>
                                </span>
                              ) : (
                                <span className="whitespace-nowrap inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-800 border border-rose-300 shadow-2xs">
                                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0"></span>
                                  <span>{r.quality_grade?.replace('_', ' ') || 'Below Std'}</span>
                                </span>
                              )}
                            </td>
                            <td className="px-3.5 py-3 text-right font-mono font-bold text-emerald-700 text-sm whitespace-nowrap">
                              ₹{(r.procurement_amount || 0).toLocaleString('en-IN')}
                            </td>
                            <td className="px-3.5 py-3 text-center whitespace-nowrap">
                              {r.status === 'COMPLETED' || r.payment_status === 'COMPLETED' || !r.status || r.status === 'SUCCESS' ? (
                                <span className="whitespace-nowrap inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-300 shadow-2xs">
                                  <span className="text-xs font-bold text-emerald-600">✓</span>
                                  <span>Paid (DBT)</span>
                                </span>
                              ) : r.status === 'IN_PROGRESS' || r.status === 'PROCESSING' ? (
                                <span className="whitespace-nowrap inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-300 shadow-2xs">
                                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse shrink-0"></span>
                                  <span>Processing</span>
                                </span>
                              ) : (
                                <span className="whitespace-nowrap inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-300 shadow-2xs">
                                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 shrink-0"></span>
                                  <span>{r.status?.replace('_', ' ') || 'Pending'}</span>
                                </span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-right whitespace-nowrap">
                              <button
                                onClick={() => setSelectedReceipt(r)}
                                className="whitespace-nowrap bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 text-xs font-bold px-3.5 py-1.5 rounded-xl transition-all cursor-pointer inline-flex items-center gap-1.5 shadow-2xs hover:shadow-xs active:scale-95"
                              >
                                <span>👁️</span>
                                <span>Receipt</span>
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Official Mandi Procurement Digital Receipt Modal */}
      <ProcurementReceiptModal
        receipt={selectedReceipt}
        isOpen={Boolean(selectedReceipt)}
        onClose={() => setSelectedReceipt(null)}
      />
    </div>
  );
}
