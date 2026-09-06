'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/auth-context';
import { notificationsApi } from '@/lib/api';
import NotificationDetailModal from '@/components/NotificationDetailModal';

export default function NotificationsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [notifications, setNotifications] = useState<any[]>([]);
  const [fetching, setFetching] = useState(true);
  const [selectedNotification, setSelectedNotification] = useState<any | null>(null);
  const [activeFilter, setActiveFilter] = useState<'ALL' | 'UNREAD' | 'CALLS' | 'PAYMENTS' | 'PROCUREMENTS' | 'BOOKINGS'>('ALL');

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  useEffect(() => {
    notificationsApi
      .list()
      .then((data) => {
        setNotifications(data);
        const count = data.filter((n: any) => !n.is_read).length;
        if (typeof window !== 'undefined') {
          localStorage.setItem('kisansetu_unread_count', String(count));
          window.dispatchEvent(
            new CustomEvent('kisansetu_notifications_updated', {
              detail: { unreadCount: count },
            })
          );
        }
      })
      .catch(console.error)
      .finally(() => setFetching(false));
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

  const typeLabel: Record<string, string> = {
    BOOKING_CONFIRMED: 'Booking Confirmed',
    SLOT_REMINDER: 'Slot Reminder',
    QUEUE_APPROACHING: 'Queue Turn Approaching',
    FARMER_CALLED: 'Live Mandi Call',
    PROCUREMENT_STARTED: 'Inspection Started',
    PROCUREMENT_COMPLETED: 'J-Form Issued',
    PAYMENT_INITIATED: 'Payment In Transit',
    PAYMENT_COMPLETED: 'DBT Credited',
    GENERAL: 'Official Notice',
  };

  const typeBadgeColor: Record<string, string> = {
    BOOKING_CONFIRMED: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    SLOT_REMINDER: 'bg-blue-100 text-blue-800 border-blue-200',
    QUEUE_APPROACHING: 'bg-amber-100 text-amber-800 border-amber-200',
    FARMER_CALLED: 'bg-orange-100 text-orange-900 border-orange-300 font-black animate-pulse',
    PROCUREMENT_STARTED: 'bg-blue-100 text-blue-800 border-blue-200',
    PROCUREMENT_COMPLETED: 'bg-teal-100 text-teal-800 border-teal-200',
    PAYMENT_INITIATED: 'bg-blue-100 text-blue-800 border-blue-200',
    PAYMENT_COMPLETED: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    GENERAL: 'bg-slate-100 text-slate-800 border-slate-200',
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const syncUnreadCount = (count: number) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('kisansetu_unread_count', String(count));
      window.dispatchEvent(
        new CustomEvent('kisansetu_notifications_updated', {
          detail: { unreadCount: count },
        })
      );
    }
  };

  const handleOpenDetail = (n: any) => {
    setSelectedNotification(n);
    if (!n.is_read) {
      setNotifications((prev) =>
        prev.map((item) => (item.id === n.id ? { ...item, is_read: true } : item))
      );
      const nextCount = Math.max(0, unreadCount - 1);
      syncUnreadCount(nextCount);
      notificationsApi.markRead([n.id]).catch(() => {});
    }
  };

  const handleMarkAllRead = () => {
    const unreadIds = notifications.filter((n) => !n.is_read).map((n) => n.id);
    if (unreadIds.length === 0) return;
    setNotifications((prev) => prev.map((item) => ({ ...item, is_read: true })));
    syncUnreadCount(0);
    notificationsApi.markRead(unreadIds).catch(() => {});
  };

  const filteredNotifications = notifications.filter((n) => {
    if (activeFilter === 'UNREAD') {
      return !n.is_read;
    }
    if (activeFilter === 'CALLS') {
      return n.type === 'FARMER_CALLED' || n.type === 'QUEUE_APPROACHING' || n.type === 'SLOT_REMINDER';
    }
    if (activeFilter === 'PAYMENTS') {
      return n.type === 'PAYMENT_COMPLETED' || n.type === 'PAYMENT_INITIATED';
    }
    if (activeFilter === 'PROCUREMENTS') {
      return n.type === 'PROCUREMENT_COMPLETED' || n.type === 'PROCUREMENT_STARTED';
    }
    if (activeFilter === 'BOOKINGS') {
      return n.type === 'BOOKING_CONFIRMED';
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50 pb-12">
      {/* Top Navigation Bar */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-20 px-4 py-3 shadow-2xs">
        <div className="max-w-4xl mx-auto flex items-center justify-between gap-3">
          {/* Left: Back + Bell + Title */}
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => router.push('/farmer')}
              className="text-emerald-700 hover:text-emerald-800 font-bold text-sm cursor-pointer flex items-center gap-1.5 transition-colors whitespace-nowrap shrink-0 bg-emerald-50 hover:bg-emerald-100 px-3 py-1.5 rounded-xl border border-emerald-200 shadow-2xs"
            >
              <span>←</span>
              <span>Back</span>
            </button>
            <div className="h-5 w-px bg-gray-200 shrink-0"></div>
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="relative inline-flex items-center justify-center shrink-0">
                <span className="text-2xl select-none leading-none">🔔</span>
                {unreadCount > 0 && (
                  <span className="absolute -top-1.5 -right-2 bg-red-600 text-white text-[10px] font-black min-w-[18px] h-[18px] px-1 rounded-full flex items-center justify-center ring-2 ring-white shadow-xs pointer-events-none animate-in zoom-in-50 duration-200">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </div>
              <div className="truncate">
                <h1 className="font-extrabold text-gray-900 text-base sm:text-lg leading-tight truncate">
                  Mandi Notifications & Alerts
                </h1>
                <p className="text-2xs text-gray-500 truncate">
                  Official APMC & PFMS Communication Gateway
                </p>
              </div>
            </div>
          </div>

          {/* Right: Mark All Read + Total Alerts Badge */}
          <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs font-bold text-emerald-800 bg-emerald-100 hover:bg-emerald-200 border border-emerald-300 px-3 py-1.5 sm:px-3.5 sm:py-2 rounded-xl cursor-pointer transition-colors flex items-center gap-1.5 shadow-2xs active:scale-95 whitespace-nowrap shrink-0"
                title="Mark all notifications as read"
              >
                <span className="text-emerald-700 font-extrabold">✓</span>
                <span className="whitespace-nowrap">Mark All Read</span>
              </button>
            )}
            <span className="text-xs font-bold text-gray-700 bg-gray-100 px-3 py-1.5 sm:py-2 rounded-xl border border-gray-200 whitespace-nowrap shrink-0 shadow-2xs">
              {notifications.length} {notifications.length === 1 ? 'Alert' : 'Alerts'}
            </span>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-4">
        {/* Info Banner */}
        <div className="bg-gradient-to-r from-emerald-50 via-teal-50 to-blue-50 rounded-2xl p-4 border border-emerald-200/80 flex items-center justify-between gap-3 text-xs shadow-2xs">
          <div className="flex items-center gap-3">
            <span className="text-2xl shrink-0">🏛️</span>
            <div>
              <p className="font-bold text-slate-800 text-xs sm:text-sm">
                Direct APMC & Government Mandi Advisories
              </p>
              <p className="text-2xs sm:text-xs text-slate-600 mt-0.5">
                {unreadCount > 0
                  ? `You have ${unreadCount} new alert${unreadCount === 1 ? '' : 's'}. Lightly highlighted cards are unread.`
                  : 'All notifications are up-to-date. Click any card to inspect full official details and copy reference IDs.'}
              </p>
            </div>
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <button
            onClick={() => setActiveFilter('ALL')}
            className={`px-3.5 py-2 rounded-xl font-bold cursor-pointer transition-all border whitespace-nowrap shrink-0 ${
              activeFilter === 'ALL'
                ? 'bg-emerald-700 text-white border-emerald-700 shadow-xs'
                : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50 hover:border-gray-300'
            }`}
          >
            All ({notifications.length})
          </button>

          <button
            onClick={() => setActiveFilter('UNREAD')}
            className={`px-3.5 py-2 rounded-xl font-bold cursor-pointer transition-all border whitespace-nowrap shrink-0 flex items-center gap-1.5 ${
              activeFilter === 'UNREAD'
                ? 'bg-red-600 text-white border-red-600 shadow-xs'
                : unreadCount > 0
                ? 'bg-red-50 text-red-700 border-red-300 hover:bg-red-100 font-extrabold'
                : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50 hover:border-gray-300'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                unreadCount > 0 ? 'bg-red-500 animate-pulse' : 'bg-gray-400'
              }`}
            ></span>
            <span>Unread ({unreadCount})</span>
          </button>

          <button
            onClick={() => setActiveFilter('CALLS')}
            className={`px-3.5 py-2 rounded-xl font-bold cursor-pointer transition-all border whitespace-nowrap shrink-0 flex items-center gap-1.5 ${
              activeFilter === 'CALLS'
                ? 'bg-amber-600 text-white border-amber-600 shadow-xs'
                : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50 hover:border-gray-300'
            }`}
          >
            <span>📢</span>
            <span>Live Calls & Queue</span>
          </button>

          <button
            onClick={() => setActiveFilter('PAYMENTS')}
            className={`px-3.5 py-2 rounded-xl font-bold cursor-pointer transition-all border whitespace-nowrap shrink-0 flex items-center gap-1.5 ${
              activeFilter === 'PAYMENTS'
                ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs'
                : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50 hover:border-gray-300'
            }`}
          >
            <span>💰</span>
            <span>Payments (DBT)</span>
          </button>

          <button
            onClick={() => setActiveFilter('PROCUREMENTS')}
            className={`px-3.5 py-2 rounded-xl font-bold cursor-pointer transition-all border whitespace-nowrap shrink-0 flex items-center gap-1.5 ${
              activeFilter === 'PROCUREMENTS'
                ? 'bg-teal-600 text-white border-teal-600 shadow-xs'
                : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50 hover:border-gray-300'
            }`}
          >
            <span>📦</span>
            <span>J-Forms</span>
          </button>

          <button
            onClick={() => setActiveFilter('BOOKINGS')}
            className={`px-3.5 py-2 rounded-xl font-bold cursor-pointer transition-all border whitespace-nowrap shrink-0 flex items-center gap-1.5 ${
              activeFilter === 'BOOKINGS'
                ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50 hover:border-gray-300'
            }`}
          >
            <span>✅</span>
            <span>Bookings</span>
          </button>
        </div>

        {/* Loading Skeleton */}
        {fetching && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-2xl p-5 border border-gray-200 animate-pulse flex items-start gap-4">
                <div className="w-12 h-12 bg-gray-200 rounded-2xl shrink-0"></div>
                <div className="flex-1 space-y-2.5">
                  <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                  <div className="h-3 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-2.5 bg-gray-200 rounded w-1/4"></div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!fetching && filteredNotifications.length === 0 && (
          <div className="bg-white rounded-2xl p-10 text-center border border-gray-200 shadow-2xs">
            {activeFilter === 'UNREAD' ? (
              <>
                <p className="text-4xl mb-3">🎉</p>
                <p className="text-gray-900 font-bold text-base">You're all caught up!</p>
                <p className="text-xs text-gray-500 mt-1">
                  You have 0 unread alerts. All mandi notifications have been reviewed.
                </p>
                <button
                  onClick={() => setActiveFilter('ALL')}
                  className="mt-4 bg-emerald-700 hover:bg-emerald-800 text-white px-5 py-2 rounded-xl text-xs font-bold cursor-pointer transition-colors shadow-xs"
                >
                  View All Notifications ({notifications.length})
                </button>
              </>
            ) : (
              <>
                <p className="text-4xl mb-3">📭</p>
                <p className="text-gray-700 font-bold">No notifications found.</p>
                <p className="text-xs text-gray-500 mt-1">
                  {activeFilter === 'ALL'
                    ? 'You do not have any alerts yet.'
                    : `No notifications under the ${activeFilter} category.`}
                </p>
                {activeFilter !== 'ALL' && (
                  <button
                    onClick={() => setActiveFilter('ALL')}
                    className="mt-3 text-xs font-semibold text-emerald-700 hover:underline cursor-pointer"
                  >
                    Clear filter and view all
                  </button>
                )}
              </>
            )}
          </div>
        )}

        {/* Notifications List */}
        {!fetching &&
          filteredNotifications.map((n) => {
            const isUnread = !n.is_read;
            const badgeColor = typeBadgeColor[n.type] || 'bg-gray-100 text-gray-800 border-gray-200';
            const icon = typeIcon[n.type] || '📋';
            const label = typeLabel[n.type] || 'Notice';

            // Extract token or amount for quick badge
            const tokenMatch = n.message?.match(/token[:\s—\-]+([A-Z0-9]+)/i) || n.title?.match(/Token\s+([A-Z0-9]+)/i);
            const token = tokenMatch ? tokenMatch[1] : null;

            const amountMatch = n.message?.match(/₹\s*([0-9,]+)/) || n.message?.match(/Rs\.?\s*([0-9,]+)/i);
            const amount = amountMatch ? amountMatch[1] : null;

            const refMatch = n.message?.match(/(BK-[A-Z0-9-]+|RCP-[A-Z0-9-]+|TXN-[A-Z0-9-]+)/i);
            const refNumber = refMatch ? refMatch[1] : null;

            return (
              <div
                key={n.id}
                onClick={() => handleOpenDetail(n)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleOpenDetail(n);
                  }
                }}
                className={`rounded-2xl p-5 border transition-all duration-150 cursor-pointer text-left relative group active:scale-[0.99] ${
                  isUnread
                    ? 'border-l-4 border-l-emerald-600 border-emerald-300/90 bg-gradient-to-r from-emerald-50/80 via-emerald-50/20 to-white shadow-xs ring-1 ring-emerald-200/60 hover:shadow-md hover:border-emerald-400'
                    : 'bg-white border-gray-200 hover:bg-slate-50/60 hover:border-gray-300 hover:shadow-xs'
                }`}
              >
                <div className="flex items-start gap-4">
                  {/* Icon Box */}
                  <div
                    className={`w-12 h-12 rounded-2xl flex items-center justify-center text-2xl shrink-0 group-hover:scale-105 transition-all shadow-2xs ${
                      isUnread
                        ? 'bg-emerald-100 text-emerald-900 border border-emerald-300 ring-2 ring-emerald-100'
                        : 'bg-slate-50 border border-slate-200 text-slate-700 group-hover:bg-white'
                    }`}
                  >
                    <span>{icon}</span>
                  </div>

                  {/* Body */}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <span className={`px-2.5 py-0.5 rounded-full text-3xs font-bold border whitespace-nowrap ${badgeColor}`}>
                        {label}
                      </span>
                      {token && (
                        <span className="px-2.5 py-0.5 rounded-full text-3xs font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200 whitespace-nowrap">
                          Token {token}
                        </span>
                      )}
                      {amount && (
                        <span className="px-2.5 py-0.5 rounded-full text-3xs font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 whitespace-nowrap">
                          ₹{amount}
                        </span>
                      )}
                      {isUnread && (
                        <span className="inline-flex items-center gap-1 text-3xs bg-emerald-700 text-white font-black px-2.5 py-0.5 rounded-full uppercase tracking-wider shadow-2xs whitespace-nowrap">
                          <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>
                          <span>Unread</span>
                        </span>
                      )}
                    </div>

                    <p
                      className={`text-sm sm:text-base leading-snug transition-colors ${
                        isUnread
                          ? 'font-black text-slate-950 group-hover:text-emerald-900'
                          : 'font-semibold text-slate-800 group-hover:text-gray-900'
                      }`}
                    >
                      {n.title}
                    </p>

                    <p
                      className={`text-xs sm:text-sm mt-1 leading-relaxed ${
                        isUnread ? 'text-slate-700 font-medium' : 'text-slate-500'
                      }`}
                    >
                      {n.message}
                    </p>

                    {/* Metadata Footer */}
                    <div className="flex flex-wrap items-center justify-between gap-3 mt-3.5 pt-3 border-t border-gray-100 text-xs text-gray-500">
                      <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 text-2xs text-gray-400">
                        <span className="whitespace-nowrap">
                          {new Date(n.created_at).toLocaleString('en-IN', {
                            day: '2-digit',
                            month: 'short',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                        <span>•</span>
                        <span className="text-slate-600 font-medium whitespace-nowrap">
                          {n.channel === 'SMS' ? '📱 SMS' : '🔔 In-App'}
                        </span>
                        {refNumber && (
                          <>
                            <span>•</span>
                            <span className="font-mono text-slate-600 font-medium whitespace-nowrap">
                              {refNumber}
                            </span>
                          </>
                        )}
                        {!isUnread && (
                          <>
                            <span>•</span>
                            <span className="text-emerald-700 font-semibold whitespace-nowrap">
                              ✓ Read
                            </span>
                          </>
                        )}
                      </div>

                      <div
                        className={`flex items-center gap-1.5 text-xs font-bold transition-colors shrink-0 whitespace-nowrap ${
                          isUnread
                            ? 'text-emerald-800 font-extrabold group-hover:text-emerald-900'
                            : 'text-gray-500 group-hover:text-emerald-700'
                        }`}
                      >
                        <span>{isUnread ? 'Tap to Read' : 'View Details'}</span>
                        <span className="group-hover:translate-x-1 transition-transform">→</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
      </div>

      {/* Detail Pop-up Card Modal */}
      <NotificationDetailModal
        notification={selectedNotification}
        isOpen={!!selectedNotification}
        onClose={() => setSelectedNotification(null)}
      />
    </div>
  );
}
