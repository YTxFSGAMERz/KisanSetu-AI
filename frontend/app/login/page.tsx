'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/auth-context';

function LoginContent() {
  const { login, demoLogin, user, loading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const demoParam = searchParams.get('demo');

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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
      setError(err.message || 'Demo login failed. Make sure the backend is running.');
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
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-700 rounded-2xl text-3xl mb-4 shadow-md">🌾</div>
          <h1 className="text-2xl font-bold text-gray-900">KisanSetu AI</h1>
          <p className="text-sm text-gray-500 mt-1">Smart Procurement Management</p>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm mb-6">
            ⚠️ {error}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
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
              className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              required
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-green-700 text-white py-3 rounded-lg font-semibold hover:bg-green-800 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {submitting ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        {/* Divider */}
        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200" />
          </div>
          <div className="relative flex justify-center text-xs text-gray-500">
            <span className="bg-white px-3">Or demo login as</span>
          </div>
        </div>

        {/* Demo Buttons */}
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={() => handleDemoLogin('farmer')}
            disabled={submitting}
            className="flex flex-col items-center justify-center gap-1 border-2 border-green-200 bg-green-50 text-green-800 rounded-xl py-3 px-2 text-xs font-semibold hover:bg-green-100 transition-colors disabled:opacity-50"
          >
            <span className="text-xl">👨‍🌾</span>
            <span>Farmer</span>
          </button>
          <button
            onClick={() => handleDemoLogin('officer')}
            disabled={submitting}
            className="flex flex-col items-center justify-center gap-1 border-2 border-blue-200 bg-blue-50 text-blue-800 rounded-xl py-3 px-2 text-xs font-semibold hover:bg-blue-100 transition-colors disabled:opacity-50"
          >
            <span className="text-xl">🏛️</span>
            <span>Officer</span>
          </button>
          <button
            onClick={() => handleDemoLogin('admin')}
            disabled={submitting}
            className="flex flex-col items-center justify-center gap-1 border-2 border-amber-200 bg-amber-50 text-amber-800 rounded-xl py-3 px-2 text-xs font-semibold hover:bg-amber-100 transition-colors disabled:opacity-50"
          >
            <span className="text-xl">📊</span>
            <span>Admin</span>
          </button>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
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
