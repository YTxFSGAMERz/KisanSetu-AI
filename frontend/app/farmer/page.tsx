'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/auth-context';
import { farmerApi } from '@/lib/api';

export default function FarmerDashboard() {
  const { user, logout, loading } = useAuth();
  const router = useRouter();
  const [dashboard, setDashboard] = useState<any>(null);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    if (!loading && !user) router.push('/login');
    if (!loading && user && user.role !== 'FARMER') {
      if (user.role === 'PROCUREMENT_OFFICER') router.push('/officer');
      else router.push('/admin');
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user?.role === 'FARMER') {
      const loadDashboard = () => {
        farmerApi.dashboard()
          .then((data) => {
            const cachedUnread = localStorage.getItem('kisansetu_unread_count');
            if (cachedUnread !== null && !isNaN(Number(cachedUnread))) {
              setDashboard({ ...data, unread_notifications: Number(cachedUnread) });
            } else {
              setDashboard(data);
            }
          })
          .catch(console.error)
          .finally(() => setFetching(false));
      };
      loadDashboard();
      window.addEventListener('focus', loadDashboard);

      const handleUpdate = (e: any) => {
        if (e.detail && typeof e.detail.unreadCount === 'number') {
          setDashboard((prev: any) =>
            prev ? { ...prev, unread_notifications: e.detail.unreadCount } : prev
          );
        } else {
          loadDashboard();
        }
      };
      window.addEventListener('kisansetu_notifications_updated', handleUpdate);

      return () => {
        window.removeEventListener('focus', loadDashboard);
        window.removeEventListener('kisansetu_notifications_updated', handleUpdate);
      };
    }
  }, [user]);

  if (loading || fetching || !user) {
    return (
      <div className="min-h-screen bg-green-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-3 animate-pulse">🌾</div>
          <p className="text-gray-500">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  const token = dashboard?.current_token;
  const slot = dashboard?.upcoming_slot;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">🌾</span>
            <div>
              <h1 className="font-bold text-green-900 text-sm">KisanSetu AI</h1>
              <p className="text-xs text-gray-500">Farmer Portal</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/farmer/notifications"
              className="p-2 rounded-xl text-gray-700 hover:text-emerald-700 hover:bg-emerald-50 transition-colors inline-flex items-center justify-center"
              title="Notifications & Alerts"
            >
              <div className="relative inline-flex items-center justify-center">
                <span className="text-xl select-none leading-none">🔔</span>
                {(dashboard?.unread_notifications ?? 0) > 0 && (
                  <span className="absolute -top-1.5 -right-2 bg-red-600 text-white text-[10px] font-black min-w-[18px] h-[18px] px-1 rounded-full flex items-center justify-center ring-2 ring-white shadow-xs pointer-events-none">
                    {dashboard.unread_notifications > 99 ? '99+' : dashboard.unread_notifications}
                  </span>
                )}
              </div>
            </Link>
            <button
              onClick={() => { logout(); router.push('/'); }}
              className="text-xs text-gray-500 hover:text-red-600 px-2 py-1 rounded"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Welcome */}
        <div className="bg-gradient-to-r from-green-700 to-emerald-600 rounded-2xl p-6 text-white">
          <p className="text-green-100 text-sm mb-1">Welcome back,</p>
          <h2 className="text-2xl font-bold">{user.name}</h2>
          {dashboard?.farmer && (
            <p className="text-green-200 text-sm mt-1">
              FRN: {dashboard.farmer.farmer_registration_number} • {dashboard.farmer.district}, {dashboard.farmer.state}
            </p>
          )}
          <p className="mt-3 text-green-100 text-sm">
            Total Payments Received: <span className="font-bold text-white text-lg">₹{(dashboard?.total_amount_received ?? 0).toLocaleString('en-IN')}</span>
          </p>
        </div>

        {/* Bank Account Warning */}
        {dashboard?.farmer && !dashboard.farmer.has_bank_account && (
          <Link
            href="/farmer/profile"
            className="flex items-center gap-3 bg-amber-50 border border-amber-300 rounded-2xl px-4 py-3 hover:bg-amber-100 transition-colors"
          >
            <span className="text-2xl">🏦</span>
            <div className="flex-1">
              <p className="font-bold text-amber-900 text-sm">Link Your Bank Account</p>
              <p className="text-xs text-amber-700">Required for MSP payment transfer. Add bank details in your profile.</p>
            </div>
            <span className="text-amber-700 text-sm">→</span>
          </Link>
        )}

        {/* Live Token Card */}
        {token && (
          <div className={`rounded-2xl p-6 border-2 ${token.status === 'CALLED' ? 'border-blue-400 bg-blue-50' : 'border-green-300 bg-white'}`}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-gray-900 text-lg">🎫 Your Live Queue Token</h3>
              {token.status === 'CALLED' && (
                <span className="bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-full animate-pulse">
                  PLEASE PROCEED TO COUNTER!
                </span>
              )}
            </div>
            <div className="flex items-center gap-6">
              <div className={`text-5xl font-extrabold font-mono rounded-2xl px-6 py-4 ${token.status === 'CALLED' ? 'bg-blue-600 text-white token-pulse' : 'bg-green-100 text-green-800'}`}>
                {token.token_number}
              </div>
              <div className="flex-1 grid grid-cols-2 gap-3 text-sm">
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 shadow-xs">
                  <p className="text-slate-600 font-medium text-xs mb-1">Status</p>
                  <p className="font-bold text-slate-900 capitalize">{token.status.replace('_', ' ')}</p>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 shadow-xs">
                  <p className="text-slate-600 font-medium text-xs mb-1">Farmers Ahead</p>
                  <p className="font-extrabold text-xl text-amber-600">{token.farmers_ahead}</p>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 shadow-xs">
                  <p className="text-slate-600 font-medium text-xs mb-1">Est. Wait</p>
                  <p className="font-bold text-slate-900">{token.estimated_wait_minutes} min</p>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 shadow-xs">
                  <p className="text-slate-600 font-medium text-xs mb-1">Queue Position</p>
                  <p className="font-bold text-slate-900">#{token.queue_position}</p>
                </div>
              </div>
            </div>
            <Link href={`/farmer/live-queue?booking_id=${slot?.booking_id}`} className="mt-4 block w-full text-center bg-green-700 text-white py-2 rounded-xl text-sm font-medium hover:bg-green-800 transition-colors">
              View Live Queue →
            </Link>
          </div>
        )}

        {/* Upcoming Slot */}
        {slot && (
          <div className="bg-white rounded-2xl p-6 border border-gray-200">
            <h3 className="font-bold text-gray-900 mb-4">📅 Upcoming Slot</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
              <div className="bg-slate-50 border border-slate-100 rounded-xl p-3">
                <p className="text-slate-600 font-medium text-xs">Centre</p>
                <p className="font-bold text-green-800 text-sm mt-0.5">{slot.centre_name}</p>
              </div>
              <div className="bg-slate-50 border border-slate-100 rounded-xl p-3">
                <p className="text-slate-600 font-medium text-xs">Date</p>
                <p className="font-bold text-slate-900 text-sm mt-0.5">{new Date(slot.slot_date).toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' })}</p>
              </div>
              <div className="bg-slate-50 border border-slate-100 rounded-xl p-3">
                <p className="text-slate-600 font-medium text-xs">Time</p>
                <p className="font-bold text-slate-900 text-sm mt-0.5">{slot.start_time}</p>
              </div>
              <div className="bg-slate-50 border border-slate-100 rounded-xl p-3">
                <p className="text-slate-600 font-medium text-xs">Crop & Qty</p>
                <p className="font-bold text-slate-900 text-sm mt-0.5">{slot.crop_name} — {slot.expected_quantity} Qtl</p>
              </div>
            </div>
            <p className="text-xs text-slate-500 font-medium mt-3">Booking: <span className="font-mono text-slate-700">{slot.booking_number}</span></p>
          </div>
        )}

        {/* Quick Actions */}
        <div>
          <h3 className="font-bold text-gray-900 mb-3">Quick Actions</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {ACTIONS.map((a) => {
              const isNotif = a.href === '/farmer/notifications';
              const unread = dashboard?.unread_notifications ?? 0;
              return (
                <Link
                  key={a.href}
                  href={a.href}
                  className="bg-white rounded-2xl p-5 border border-gray-200 hover:border-green-300 hover:shadow-sm transition-all text-center relative group"
                >
                  <div className="text-3xl mb-2 relative inline-block">
                    <span>{a.icon}</span>
                    {isNotif && unread > 0 && (
                      <span className="absolute -top-1 -right-2 bg-red-600 text-white text-[10px] font-black min-w-[18px] h-[18px] px-1 rounded-full flex items-center justify-center ring-2 ring-white shadow-xs">
                        {unread > 99 ? '99+' : unread}
                      </span>
                    )}
                  </div>
                  <p className="font-semibold text-gray-900 text-sm">{a.label}</p>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Recent Procurements & J-Forms */}
        {dashboard?.recent_procurements?.length > 0 && (
          <div className="bg-white rounded-2xl p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-bold text-gray-900 text-lg flex items-center gap-2">
                  <span>📜</span> Recent Mandi J-Forms (जे-फॉर्म)
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Official APMC procurement vouchers settled via PFMS Direct Benefit Transfer
                </p>
              </div>
              <Link href="/farmer/procurements" className="text-green-700 text-xs font-semibold hover:underline">
                View All ({dashboard.recent_procurements.length}) →
              </Link>
            </div>

            <div className="divide-y divide-gray-100">
              {dashboard.recent_procurements.map((p: any) => {
                const isWheat = p.crop_name?.toLowerCase().includes('wheat');
                const isMustard = p.crop_name?.toLowerCase().includes('mustard') || p.crop_name?.toLowerCase().includes('sarson');
                const cropIcon = isWheat ? '🌾' : isMustard ? '🟡' : '🌾';
                const formattedDate = p.created_at
                  ? new Date(p.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
                  : 'Recent';

                return (
                  <div key={p.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-sm hover:bg-slate-50/60 rounded-xl px-2 transition-colors">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-xl bg-green-50 border border-green-200 flex items-center justify-center text-xl shrink-0">
                        {cropIcon}
                      </div>
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="font-bold text-slate-900">{p.crop_name || 'Produce'}</p>
                          <span className="font-mono text-xs bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded-md font-semibold">
                            {p.receipt_number || p.j_form_number || `JF-HR-KNL-2026-${String(p.id).padStart(5, '0')}`}
                          </span>
                          <span className="text-[11px] bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold px-1.5 py-0.5 rounded">
                            {p.quality_grade === 'GRADE_A' ? 'Grade A (FAQ)' : (p.quality_grade || 'Grade A')}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 mt-1 flex items-center gap-1.5 flex-wrap">
                          <span>📍 {p.centre_name ? p.centre_name.split('—')[0].trim() : 'Karnal Grain Mandi'}</span>
                          <span>•</span>
                          <span>{p.accepted_quantity} Qtl {p.msp_rate ? `@ ₹${Number(p.msp_rate).toLocaleString('en-IN')}/Qtl` : ''}</span>
                          <span>•</span>
                          <span>{formattedDate}</span>
                        </p>
                      </div>
                    </div>

                    <div className="sm:text-right flex sm:flex-col justify-between items-center sm:items-end shrink-0">
                      <div>
                        <p className="font-extrabold text-green-700 text-base">
                          ₹{(p.procurement_amount ?? 0).toLocaleString('en-IN')}
                        </p>
                      </div>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-green-100 text-green-800 border border-green-200">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-600"></span>
                          PFMS DBT Credited
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const ACTIONS = [
  { icon: '📅', label: 'Book a Slot', href: '/farmer/book-slot' },
  { icon: '📡', label: 'Live Queue', href: '/farmer/live-queue' },
  { icon: '📦', label: 'My Procurements', href: '/farmer/procurements' },
  { icon: '💰', label: 'Payment Status', href: '/farmer/payments' },
  { icon: '🔔', label: 'Notifications', href: '/farmer/notifications' },
  { icon: '👤', label: 'My Profile', href: '/farmer/profile' },
];
