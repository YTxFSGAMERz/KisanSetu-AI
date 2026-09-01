'use client';

import { useEffect, useState, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/auth-context';
import { useWebSocket } from '@/context/websocket-context';
import { queueApi, bookingsApi } from '@/lib/api';

function LiveQueueContent() {
  const { user, loading } = useAuth();
  const { lastMessage, connectToQueue, isConnected } = useWebSocket();
  const router = useRouter();
  const searchParams = useSearchParams();
  const bookingId = searchParams.get('booking_id');

  const [queueStatus, setQueueStatus] = useState<any>(null);
  const [myToken, setMyToken] = useState<any>(null);
  const [centreId, setCentreId] = useState<number | null>(null);
  const [fetching, setFetching] = useState(true);
  const [calledAlert, setCalledAlert] = useState(false);

  const fetchQueueData = useCallback(async (cId: number) => {
    const status = await queueApi.status(cId);
    setQueueStatus(status);
  }, []);

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  useEffect(() => {
    if (!bookingId) return;
    (async () => {
      try {
        const booking = await bookingsApi.get(Number(bookingId));
        const token = await queueApi.getByBooking(Number(bookingId));
        setMyToken(token);
        setCentreId(booking.centre_id);
        await fetchQueueData(booking.centre_id);
        connectToQueue(booking.centre_id);
      } catch (e) {
        console.error(e);
      } finally {
        setFetching(false);
      }
    })();
  }, [bookingId]);

  // Handle real-time WebSocket events
  useEffect(() => {
    if (!lastMessage) return;
    if (lastMessage.event === 'QUEUE_UPDATED' && centreId) {
      fetchQueueData(centreId);
      // Refresh personal token
      if (bookingId) {
        queueApi.getByBooking(Number(bookingId)).then(setMyToken).catch(() => {});
      }
    }
    if (lastMessage.event === 'FARMER_CALLED') {
      setCalledAlert(true);
      setTimeout(() => setCalledAlert(false), 15000);
    }
  }, [lastMessage, centreId, bookingId]);

  if (loading || fetching) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl animate-pulse mb-3">📡</div>
          <p className="text-gray-500">Connecting to live queue...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => router.push('/farmer')} className="text-green-700">← Back</button>
            <h1 className="font-bold text-gray-900">Live Queue</h1>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`} />
            <span className="text-xs text-gray-500">{isConnected ? 'Live' : 'Offline'}</span>
          </div>
        </div>
      </div>

      {/* CALLED ALERT */}
      {calledAlert && (
        <div className="bg-blue-600 text-white text-center py-4 px-4 animate-pulse">
          <p className="text-lg font-bold">🔔 TOKEN {myToken?.token_number} — PLEASE PROCEED TO COUNTER!</p>
          <p className="text-sm text-blue-100">Come to the procurement counter with your produce immediately.</p>
        </div>
      )}

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* My Token */}
        {myToken && (
          <div className={`rounded-2xl p-6 border-2 text-center ${myToken.status === 'CALLED' ? 'border-blue-500 bg-blue-50' : myToken.status === 'PROCESSING' ? 'border-purple-400 bg-purple-50' : myToken.status === 'COMPLETED' ? 'border-green-400 bg-green-50' : 'border-green-300 bg-white'}`}>
            <p className="text-xs text-gray-500 uppercase font-semibold tracking-wider mb-2">Your Token</p>
            <div className={`text-6xl font-extrabold font-mono mb-4 ${myToken.status === 'CALLED' ? 'text-blue-700 token-pulse' : 'text-green-800'}`}>
              {myToken.token_number}
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm max-w-xs mx-auto">
              <div className="bg-white rounded-xl p-3 shadow-sm">
                <p className="text-xs text-gray-400 mb-1">Status</p>
                <p className="font-bold capitalize">{myToken.status.replace('_', ' ')}</p>
              </div>
              <div className="bg-white rounded-xl p-3 shadow-sm">
                <p className="text-xs text-gray-400 mb-1">Farmers Ahead</p>
                <p className="font-bold text-2xl text-amber-600">{myToken.farmers_ahead ?? 0}</p>
              </div>
              <div className="bg-white rounded-xl p-3 shadow-sm">
                <p className="text-xs text-gray-400 mb-1">Estimated Wait</p>
                <p className="font-bold">{myToken.estimated_wait_minutes} min</p>
              </div>
              <div className="bg-white rounded-xl p-3 shadow-sm">
                <p className="text-xs text-gray-400 mb-1">Queue Position</p>
                <p className="font-bold">#{myToken.queue_position}</p>
              </div>
            </div>

            {myToken.status === 'CALLED' && (
              <div className="mt-4 bg-blue-600 text-white rounded-xl py-3 px-4 font-bold animate-pulse">
                🔔 PLEASE PROCEED TO THE COUNTER NOW!
              </div>
            )}
          </div>
        )}

        {/* Current Queue Status */}
        {queueStatus && (
          <div className="bg-white rounded-2xl p-5 border border-gray-200">
            <h3 className="font-bold text-gray-900 mb-4">Queue Status</h3>
            <div className="grid grid-cols-4 gap-3 text-center text-sm">
              <div className="bg-green-50 rounded-xl p-3">
                <p className="text-xs text-gray-500">Now Processing</p>
                <p className="font-extrabold text-xl font-mono text-green-800">{queueStatus.current_token || '—'}</p>
              </div>
              <div className="bg-amber-50 rounded-xl p-3">
                <p className="text-xs text-gray-500">Waiting</p>
                <p className="font-extrabold text-xl text-amber-600">{queueStatus.waiting_count}</p>
              </div>
              <div className="bg-blue-50 rounded-xl p-3">
                <p className="text-xs text-gray-500">Processing</p>
                <p className="font-extrabold text-xl text-blue-700">{queueStatus.processing_count}</p>
              </div>
              <div className="bg-gray-50 rounded-xl p-3">
                <p className="text-xs text-gray-500">Completed</p>
                <p className="font-extrabold text-xl text-gray-700">{queueStatus.completed_today}</p>
              </div>
            </div>
          </div>
        )}

        {/* Queue List */}
        {queueStatus?.queue?.length > 0 && (
          <div className="bg-white rounded-2xl p-5 border border-gray-200">
            <h3 className="font-bold text-gray-900 mb-3">Waiting Queue</h3>
            <div className="space-y-2">
              {queueStatus.queue.slice(0, 10).map((t: any, i: number) => (
                <div
                  key={t.id}
                  className={`flex items-center justify-between py-2 px-3 rounded-xl text-sm ${myToken?.token_number === t.token_number ? 'bg-green-100 border border-green-300' : 'bg-gray-50'}`}
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-base w-12">{t.token_number}</span>
                    {myToken?.token_number === t.token_number && <span className="text-xs bg-green-700 text-white px-1.5 py-0.5 rounded">YOU</span>}
                    <span className="text-gray-600">{t.farmer_name || 'Farmer'}</span>
                  </div>
                  <span className="text-xs text-gray-400">~{t.estimated_wait_minutes} min</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function LiveQueuePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center"><div className="text-4xl animate-pulse mb-3">📡</div><p className="text-gray-500">Loading queue...</p></div>
      </div>
    }>
      <LiveQueueContent />
    </Suspense>
  );
}
