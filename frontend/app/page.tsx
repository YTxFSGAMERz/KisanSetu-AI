'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useAuth } from '@/context/auth-context';

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      if (user.role === 'FARMER') router.push('/farmer');
      else if (user.role === 'PROCUREMENT_OFFICER') router.push('/officer');
      else router.push('/admin');
    }
  }, [user, loading, router]);

  return (
    <main className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100">
      {/* Government Header Bar */}
      <div className="bg-[#1e3a5f] text-white text-xs py-1 px-4 text-center">
        भारत सरकार | Government of India &nbsp;|&nbsp; Ministry of Consumer Affairs, Food &amp; Public Distribution
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <header className="flex items-center justify-between mb-12">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-green-700 rounded-xl flex items-center justify-center text-white text-2xl font-bold shadow-md">
              🌾
            </div>
            <div>
              <h1 className="text-2xl font-bold text-green-900">KisanSetu AI</h1>
              <p className="text-xs text-green-700">Smart Procurement. Smart Queues. Empowered Farmers.</p>
            </div>
          </div>
          <Link
            href="/login"
            className="bg-green-700 text-white px-6 py-2 rounded-lg font-medium hover:bg-green-800 transition-colors shadow-sm"
          >
            Login / Sign In
          </Link>
        </header>

        {/* Hero */}
        <section className="text-center py-16">
          <div className="inline-block bg-green-100 text-green-800 text-sm font-medium px-4 py-1 rounded-full mb-6 border border-green-200">
            🏆 Smart India Hackathon 2026 — Problem Statement 26032
          </div>
          <h2 className="text-5xl font-extrabold text-gray-900 mb-6 leading-tight">
            End Waiting. Start Earning.<br />
            <span className="text-green-700">Smarter Procurement for Every Kisan.</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-10">
            Book your procurement slot in advance. Get a live digital token. Track your queue in real time.
            Know your payment status instantly.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link
              href="/login"
              className="bg-green-700 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:bg-green-800 transition-colors shadow-lg"
            >
              Farmer Login / Register
            </Link>
            <Link
              href="/login?demo=officer"
              className="bg-white text-green-700 border-2 border-green-700 px-8 py-4 rounded-xl text-lg font-semibold hover:bg-green-50 transition-colors"
            >
              Officer Dashboard
            </Link>
            <Link
              href="/login?demo=admin"
              className="bg-amber-600 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:bg-amber-700 transition-colors shadow-lg"
            >
              Admin Analytics
            </Link>
          </div>
        </section>

        {/* Feature Cards */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {FEATURES.map((f) => (
            <div key={f.title} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="font-semibold text-gray-900 text-lg mb-2">{f.title}</h3>
              <p className="text-gray-600 text-sm">{f.desc}</p>
            </div>
          ))}
        </section>

        {/* Demo Accounts Banner */}
        <section className="bg-green-900 text-white rounded-2xl p-8 mb-12">
          <h3 className="text-xl font-bold mb-2">🎬 Quick Demo Portals</h3>
          <p className="text-xs text-green-200 mb-6">Select a role to preview the role-specific automated workflows and dashboards.</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { role: 'Farmer Portal', desc: 'Book slots, track live queues & MSP status', icon: '👨‍🌾', path: '/login?demo=farmer' },
              { role: 'Procurement Officer', desc: 'Manage queue, digital grading & receipts', icon: '🏛️', path: '/login?demo=officer' },
              { role: 'Government Admin', desc: 'National analytics, congestion & volume charts', icon: '📊', path: '/login?demo=admin' },
            ].map((d) => (
              <Link key={d.role} href={d.path}
                className="bg-white/10 hover:bg-white/20 border border-white/20 rounded-xl p-4 block transition-colors">
                <div className="flex items-center gap-2 font-semibold mb-1 text-base">
                  <span>{d.icon}</span>
                  <span>{d.role}</span>
                </div>
                <div className="text-xs text-green-200 mb-3">{d.desc}</div>
                <div className="text-xs font-medium text-white bg-green-800/80 hover:bg-green-700 rounded px-2.5 py-1.5 inline-block">
                  Open Role Portal →
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* Flow Diagram */}
        <section className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6 text-center">Complete Farmer Journey</h3>
          <div className="flex flex-wrap justify-center gap-2 items-center text-sm font-medium">
            {JOURNEY.map((step, i) => (
              <div key={step} className="flex items-center gap-2">
                <div className="bg-green-50 border border-green-200 text-green-800 px-3 py-2 rounded-lg">{step}</div>
                {i < JOURNEY.length - 1 && <span className="text-gray-400">→</span>}
              </div>
            ))}
          </div>
        </section>

        {/* Footer */}
        <footer className="text-center text-sm text-gray-500 py-4">
          <p>KisanSetu AI | SIH Problem 26032 | Department of Consumer Affairs (DoCA)</p>
          <p className="mt-1 text-xs">Prototype Version 1.0 — Smart India Hackathon 2026</p>
        </footer>
      </div>
    </main>
  );
}

const FEATURES = [
  { icon: '📅', title: 'Smart Slot Booking', desc: 'Book your procurement slot from home. No more standing in queues at Mandi gates from dawn.' },
  { icon: '🤖', title: 'AI Slot Recommendation', desc: 'Our engine predicts waiting time and congestion to suggest the best 3 slots for you.' },
  { icon: '🎫', title: 'Digital Token System', desc: 'Get a unique digital token like A042. Track exactly how many farmers are ahead of you.' },
  { icon: '📡', title: 'Real-Time Queue', desc: 'Live dashboard updates the moment the officer calls the next farmer — no manual refresh.' },
  { icon: '⚖️', title: 'Transparent Procurement', desc: 'Your crop is weighed, graded, and recorded digitally. Full transparency at every step.' },
  { icon: '💰', title: 'Payment Tracking', desc: 'Track your MSP payment from PROCESSING to COMPLETED with transaction references.' },
];

const JOURNEY = [
  'Register', 'Select Centre', 'Book Slot', 'Get Token', 'Live Queue', 'Procurement', 'Payment',
];
