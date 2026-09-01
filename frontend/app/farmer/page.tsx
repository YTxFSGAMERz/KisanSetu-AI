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
      farmerApi.dashboard()
        .then(setDashboard)
        .catch(console.error)
        .finally(() => setFetching(false));
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
            <Link href="/farmer/notifications" className="relative p-2">
              <span className="text-xl">🔔</span>
              {(dashboard?.unread_notifications ?? 0) > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs w-4 h-4 rounded-full flex items-center justify-center">
                  {dashboard.unread_notifications}
                </span>
              )}
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
                <div className="bg-gray-50 rounded-xl p-3">
                  <p className="text-gray-500 text-xs mb-1">Status</p>
                  <p className="font-semibold capitalize">{token.status.replace('_', ' ')}</p>
                </div>
                <div className="bg-gray-50 rounded-xl p-3">
                  <p className="text-gray-500 text-xs mb-1">Farmers Ahead</p>
                  <p className="font-semibold text-xl">{token.farmers_ahead}</p>
                </div>
                <div className="bg-gray-50 rounded-xl p-3">
                  <p className="text-gray-500 text-xs mb-1">Est. Wait</p>
                  <p className="font-semibold">{token.estimated_wait_minutes} min</p>
                </div>
                <div className="bg-gray-50 rounded-xl p-3">
                  <p className="text-gray-500 text-xs mb-1">Queue Position</p>
                  <p className="font-semibold">#{token.queue_position}</p>
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
              <div>
                <p className="text-gray-500 text-xs">Centre</p>
                <p className="font-semibold text-green-800">{slot.centre_name}</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs">Date</p>
                <p className="font-semibold">{new Date(slot.slot_date).toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' })}</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs">Time</p>
                <p className="font-semibold">{slot.start_time}</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs">Crop & Qty</p>
                <p className="font-semibold">{slot.crop_name} — {slot.expected_quantity} Qtl</p>
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-3">Booking: {slot.booking_number}</p>
          </div>
        )}

        {/* Quick Actions */}
        <div>
          <h3 className="font-bold text-gray-900 mb-3">Quick Actions</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {ACTIONS.map((a) => (
              <Link
                key={a.href}
                href={a.href}
                className="bg-white rounded-2xl p-5 border border-gray-200 hover:border-green-300 hover:shadow-sm transition-all text-center"
              >
                <div className="text-3xl mb-2">{a.icon}</div>
                <p className="font-medium text-gray-900 text-sm">{a.label}</p>
              </Link>
            ))}
          </div>
        </div>

        {/* Recent Procurements */}
        {dashboard?.recent_procurements?.length > 0 && (
          <div className="bg-white rounded-2xl p-6 border border-gray-200">
            <h3 className="font-bold text-gray-900 mb-4">Recent Procurements</h3>
            <div className="space-y-3">
              {dashboard.recent_procurements.map((p: any) => (
                <div key={p.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0 text-sm">
                  <div>
                    <p className="font-medium">{p.receipt_number || `Procurement #${p.id}`}</p>
                    <p className="text-xs text-gray-500">{p.accepted_quantity} Qtl accepted</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-green-700">₹{(p.procurement_amount ?? 0).toLocaleString('en-IN')}</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${p.status === 'COMPLETED' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                      {p.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <Link href="/farmer/procurements" className="mt-3 block text-center text-green-700 text-sm font-medium">
              View All →
            </Link>
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
