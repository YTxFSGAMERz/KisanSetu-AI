'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/auth-context';
import { notificationsApi } from '@/lib/api';

export default function NotificationsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [notifications, setNotifications] = useState<any[]>([]);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  useEffect(() => {
    notificationsApi.list().then((data) => {
      setNotifications(data);
      const unread = data.filter((n: any) => !n.is_read).map((n: any) => n.id);
      if (unread.length > 0) notificationsApi.markRead(unread).catch(() => {});
    }).catch(console.error).finally(() => setFetching(false));
  }, []);

  const typeIcon: Record<string, string> = {
    BOOKING_CONFIRMED: '✅',
    SLOT_REMINDER: '🔔',
    QUEUE_APPROACHING: '⏰',
    FARMER_CALLED: '📢',
    PROCUREMENT_STARTED: '⚖️',
    PROCUREMENT_COMPLETED: '📦',
    PAYMENT_INITIATED: '💳',
    PAYMENT_COMPLETED: '💰',
    GENERAL: '📋',
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <button onClick={() => router.push('/farmer')} className="text-green-700">← Back</button>
          <h1 className="font-bold text-gray-900">Notifications</h1>
        </div>
      </div>
      <div className="max-w-2xl mx-auto px-4 py-6 space-y-3">
        {fetching && <div className="text-center text-gray-400 py-8 animate-pulse">Loading notifications...</div>}
        {!fetching && notifications.length === 0 && (
          <div className="bg-white rounded-2xl p-8 text-center border border-gray-200">
            <p className="text-4xl mb-3">🔔</p>
            <p className="text-gray-600">No notifications yet.</p>
          </div>
        )}
        {notifications.map((n) => (
          <div key={n.id} className={`bg-white rounded-2xl p-4 border ${!n.is_read ? 'border-green-300 bg-green-50' : 'border-gray-200'}`}>
            <div className="flex items-start gap-3">
              <span className="text-xl">{typeIcon[n.type] || '📋'}</span>
              <div className="flex-1">
                <p className="font-semibold text-gray-900 text-sm">{n.title}</p>
                <p className="text-sm text-gray-600 mt-1">{n.message}</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs text-gray-400">{new Date(n.created_at).toLocaleString('en-IN')}</span>
                  {!n.is_read && <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-medium">New</span>}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
