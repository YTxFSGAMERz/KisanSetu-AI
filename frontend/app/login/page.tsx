'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth, DEMO_CREDENTIALS } from '@/context/auth-context';

function LoginContent() {
  const { login, demoLogin, user, loading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const demoParam = searchParams.get('demo');

  const [email, setEmail] = useState('demo.farmer@example.com');
  const [password, setPassword] = useState('Farmer123!');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Auto-trigger demo login if ?demo=farmer|officer|admin
  useEffect(() => {
    if (demoParam && !loading && !user) {
      const role = demoParam as 'farmer' | 'officer' | 'admin';
      if (['farmer', 'officer', 'admin'].includes(role)) {
        handleDemoLogin(role);
      }
    }
  }, [demoParam, loading, user]);

  useEffect(() => {
    if (!loading && user) {
      redirectByRole(user.role);
    }
  }, [user, loading]);

  function redirectByRole(role: string) {
    if (role === 'FARMER') router.push('/farmer');
    else if (role === 'PROCUREMENT_OFFICER') router.push('/officer');
    else router.push('/admin');
  }

  const fillCredentials = (role: 'farmer' | 'officer' | 'admin') => {
    const cred = DEMO_CREDENTIALS[role];
    setEmail(cred.emails[0]);
    setPassword(cred.password);
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDemoLogin = async (role: 'farmer' | 'officer' | 'admin') => {
    setError('');
    setSubmitting(true);
    try {
      await demoLogin(role);
    } catch (err: any) {
      setError(err.message || 'Demo login failed.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading || (demoParam && submitting)) {
    return (
      <div className="min-h-screen bg-green-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">🌾</div>
          <p className="text-gray-600 font-medium">Loading KisanSetu AI...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
        {/* Logo */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-700 rounded-2xl text-3xl mb-3 shadow-md">🌾</div>
          <h1 className="text-2xl font-bold text-gray-900">KisanSetu AI</h1>
          <p className="text-sm text-gray-500 mt-1">Smart Procurement Management</p>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm mb-6 flex items-start gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* 1-Click Instant Demo Login */}
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2.5 text-center">
            🚀 1-Click Instant Demo Login
          </p>
          <div className="grid grid-cols-3 gap-2.5">
            <button
              type="button"
              onClick={() => handleDemoLogin('farmer')}
              disabled={submitting}
              className="flex flex-col items-center justify-center gap-1 border-2 border-green-200 bg-green-50 text-green-800 rounded-xl py-2.5 px-2 text-xs font-semibold hover:bg-green-100 hover:border-green-400 active:scale-95 transition-all shadow-sm disabled:opacity-50"
            >
              <span className="text-xl">👨‍🌾</span>
              <span>Farmer</span>
            </button>
            <button
              type="button"
              onClick={() => handleDemoLogin('officer')}
              disabled={submitting}
              className="flex flex-col items-center justify-center gap-1 border-2 border-blue-200 bg-blue-50 text-blue-800 rounded-xl py-2.5 px-2 text-xs font-semibold hover:bg-blue-100 hover:border-blue-400 active:scale-95 transition-all shadow-sm disabled:opacity-50"
            >
              <span className="text-xl">🏛️</span>
              <span>Officer</span>
            </button>
            <button
              type="button"
              onClick={() => handleDemoLogin('admin')}
              disabled={submitting}
              className="flex flex-col items-center justify-center gap-1 border-2 border-amber-200 bg-amber-50 text-amber-800 rounded-xl py-2.5 px-2 text-xs font-semibold hover:bg-amber-100 hover:border-amber-400 active:scale-95 transition-all shadow-sm disabled:opacity-50"
            >
              <span className="text-xl">📊</span>
              <span>Admin</span>
            </button>
          </div>
        </div>

        {/* Divider */}
        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200" />
          </div>
          <div className="relative flex justify-center text-xs text-gray-500">
            <span className="bg-white px-3">Or sign in with hardcoded credentials</span>
          </div>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4 mb-5">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm font-medium text-gray-700">Email Address</label>
              <span className="text-[11px] text-gray-400">Demo enabled</span>
            </div>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="demo.farmer@example.com"
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-gray-900"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-gray-900"
              required
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-green-700 text-white py-2.5 rounded-lg font-semibold hover:bg-green-800 transition-colors shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {submitting ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        {/* Quick Fill Demo Credentials Reference */}
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-3 text-xs text-gray-600">
          <p className="font-semibold text-gray-700 mb-1.5 flex items-center justify-between">
            <span>🔑 Hardcoded Demo Credentials:</span>
            <span className="text-[10px] text-gray-400">Click to fill</span>
          </p>
          <div className="space-y-1 font-mono text-[11px]">
            <button
              type="button"
              onClick={() => fillCredentials('farmer')}
              className="w-full text-left px-2 py-1 rounded hover:bg-white flex items-center justify-between transition-colors border border-transparent hover:border-gray-200"
            >
              <span>👨‍🌾 <b>Farmer:</b> demo.farmer@example.com</span>
              <span className="text-green-700 font-semibold">Farmer123!</span>
            </button>
            <button
              type="button"
              onClick={() => fillCredentials('officer')}
              className="w-full text-left px-2 py-1 rounded hover:bg-white flex items-center justify-between transition-colors border border-transparent hover:border-gray-200"
            >
              <span>🏛️ <b>Officer:</b> demo.officer@example.com</span>
              <span className="text-blue-700 font-semibold">Officer123!</span>
            </button>
            <button
              type="button"
              onClick={() => fillCredentials('admin')}
              className="w-full text-left px-2 py-1 rounded hover:bg-white flex items-center justify-between transition-colors border border-transparent hover:border-gray-200"
            >
              <span>📊 <b>Admin:</b> demo.admin@example.com</span>
              <span className="text-amber-700 font-semibold">Admin123!</span>
            </button>
          </div>
        </div>

        <p className="text-center text-xs text-gray-400 mt-5">
          SIH Problem 26032 | Department of Consumer Affairs
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-green-50 flex items-center justify-center">
        <div className="text-center"><div className="text-4xl mb-4">🌾</div><p className="text-gray-600 font-medium">Loading KisanSetu AI...</p></div>
      </div>
    }>
      <LoginContent />
    </Suspense>
  );
}
