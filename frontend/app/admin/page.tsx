'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/auth-context';
import { analyticsApi } from '@/lib/api';

export default function AdminDashboard() {
  const { user, logout, loading } = useAuth();
  const router = useRouter();
  const [dashboard, setDashboard] = useState<any>(null);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    if (!loading && !user) router.push('/login');
    if (!loading && user && user.role === 'FARMER') router.push('/farmer');
    if (!loading && user && user.role === 'PROCUREMENT_OFFICER') router.push('/officer');
  }, [user, loading, router]);

  useEffect(() => {
    analyticsApi.adminDashboard()
      .then(setDashboard)
      .catch(console.error)
      .finally(() => setFetching(false));
  }, []);

  if (loading || fetching) {
    return <div className="min-h-screen bg-slate-50 flex items-center justify-center"><div className="text-3xl animate-pulse">📊</div></div>;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <nav className="bg-[#1e3a5f] text-white px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">🏛️</span>
            <div>
              <h1 className="font-bold text-sm">KisanSetu AI — Government Analytics</h1>
              <p className="text-xs text-blue-300">Ministry of Consumer Affairs, Food & Public Distribution</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-blue-300">{user?.name}</span>
            <button onClick={() => { logout(); router.push('/'); }} className="text-xs text-blue-300 hover:text-white">Logout</button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* National KPI Cards */}
        <div>
          <h2 className="font-bold text-gray-800 mb-3">National Procurement Overview</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              { icon: '🏭', label: 'Active Centres', value: dashboard?.total_active_centres || 0, suffix: '', color: 'border-blue-300' },
              { icon: '👨‍🌾', label: 'Registered Farmers', value: (dashboard?.total_registered_farmers || 0).toLocaleString('en-IN'), suffix: '', color: 'border-green-300' },
              { icon: '✅', label: 'Served Today', value: dashboard?.farmers_served_today || 0, suffix: '', color: 'border-emerald-300' },
              { icon: '⏱️', label: 'Avg Wait (min)', value: dashboard?.avg_waiting_minutes || 0, suffix: '', color: 'border-amber-300' },
              { icon: '⚖️', label: 'Total Procured', value: (dashboard?.total_procurement_quintals || 0).toFixed(0), suffix: ' Qtl', color: 'border-indigo-300' },
              { icon: '💰', label: 'Payment Rate', value: dashboard?.payment_completion_rate || 0, suffix: '%', color: 'border-pink-300' },
            ].map((kpi) => (
              <div key={kpi.label} className={`bg-white rounded-2xl p-4 border-l-4 ${kpi.color} shadow-sm`}>
                <p className="text-2xl mb-1">{kpi.icon}</p>
                <p className="text-xs text-gray-500">{kpi.label}</p>
                <p className="text-xl font-extrabold text-gray-900">{kpi.value}{kpi.suffix}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Centre-by-Centre Analytics */}
        <div>
          <h2 className="font-bold text-gray-800 mb-3">Procurement Centre Status</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {dashboard?.centres?.map((c: any) => (
              <div key={c.centre_id} className="bg-white rounded-2xl p-5 border border-gray-200 shadow-sm">
                <h3 className="font-semibold text-gray-900 text-sm mb-3 leading-tight">{c.centre_name}</h3>

                {/* Congestion Meter */}
                <div className="mb-3">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>Congestion</span>
                    <span className={`font-bold ${c.congestion_score < 25 ? 'text-green-700' : c.congestion_score < 50 ? 'text-amber-700' : c.congestion_score < 75 ? 'text-orange-700' : 'text-red-700'}`}>
                      {c.congestion_score.toFixed(0)}/100
                    </span>
                  </div>
                  <div className="bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${c.congestion_score < 25 ? 'bg-green-500' : c.congestion_score < 50 ? 'bg-amber-500' : c.congestion_score < 75 ? 'bg-orange-500' : 'bg-red-600'}`}
                      style={{ width: `${c.congestion_score}%` }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="bg-green-50 rounded-lg p-2">
                    <p className="text-xs text-gray-400">Completed</p>
                    <p className="font-bold text-green-700">{c.completed_today}</p>
                  </div>
                  <div className="bg-red-50 rounded-lg p-2">
                    <p className="text-xs text-gray-400">No Shows</p>
                    <p className="font-bold text-red-600">{c.no_shows_today}</p>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-2">
                    <p className="text-xs text-gray-400">Quantity (Qtl)</p>
                    <p className="font-bold text-blue-700">{(c.total_quantity_kg || 0).toFixed(1)}</p>
                  </div>
                  <div className="bg-indigo-50 rounded-lg p-2">
                    <p className="text-xs text-gray-400">Proc. Time</p>
                    <p className="font-bold">{c.avg_processing_minutes} min</p>
                  </div>
                </div>

                {c.total_amount > 0 && (
                  <div className="mt-3 bg-green-50 rounded-lg px-3 py-2 flex justify-between text-sm">
                    <span className="text-green-700 font-medium">Total Disbursed</span>
                    <span className="font-bold text-green-800">₹{(c.total_amount || 0).toLocaleString('en-IN')}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Daily Volume Chart (text-based) */}
        {dashboard?.daily_volume_chart && (
          <div className="bg-white rounded-2xl p-6 border border-gray-200">
            <h2 className="font-bold text-gray-800 mb-4">📈 7-Day Procurement Volume</h2>
            <div className="space-y-2">
              {dashboard.daily_volume_chart.map((d: any) => {
                const maxQty = Math.max(...dashboard.daily_volume_chart.map((x: any) => x.quantity), 1);
                const pct = Math.round((d.quantity / maxQty) * 100);
                return (
                  <div key={d.date} className="flex items-center gap-3 text-sm">
                    <span className="w-24 text-xs text-gray-500 shrink-0">{new Date(d.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</span>
                    <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                      <div className="bg-green-600 h-5 rounded-full flex items-center pl-2 text-white text-xs font-medium transition-all" style={{ width: `${Math.max(pct, 2)}%` }}>
                        {d.quantity > 0 ? `${d.quantity.toFixed(0)} Qtl` : ''}
                      </div>
                    </div>
                    <span className="text-xs text-gray-400 shrink-0">{d.count} farmers</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Summary Footer */}
        <div className="bg-[#1e3a5f] text-white rounded-2xl p-5 text-sm">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            <div>
              <p className="text-blue-300 text-xs">No-Show Rate</p>
              <p className="font-bold text-lg">{dashboard?.no_show_rate || 0}%</p>
            </div>
            <div>
              <p className="text-blue-300 text-xs">Payment Completion</p>
              <p className="font-bold text-lg">{dashboard?.payment_completion_rate || 0}%</p>
            </div>
            <div>
              <p className="text-blue-300 text-xs">Avg Wait Time</p>
              <p className="font-bold text-lg">{dashboard?.avg_waiting_minutes || 0} min</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
