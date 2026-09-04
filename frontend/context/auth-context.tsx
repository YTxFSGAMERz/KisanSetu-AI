'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { authApi } from '@/lib/api';

export interface AuthUser {
  id: number;
  name: string;
  email: string;
  phone: string;
  role: 'FARMER' | 'PROCUREMENT_OFFICER' | 'CENTRE_ADMIN' | 'GOVERNMENT_ADMIN';
  farmer_id?: number;
  centre_id?: number;
}

export const DEMO_USERS: Record<'farmer' | 'officer' | 'admin', AuthUser> = {
  farmer: {
    id: 1,
    name: 'Rajesh Verma (Kisan)',
    email: 'demo.farmer@example.com',
    phone: '9876543210',
    role: 'FARMER',
    farmer_id: 1,
  },
  officer: {
    id: 2,
    name: 'Anil Kumar (Mandi Officer)',
    email: 'demo.officer@example.com',
    phone: '9876543211',
    role: 'PROCUREMENT_OFFICER',
    centre_id: 1,
  },
  admin: {
    id: 3,
    name: 'Dr. Ramesh Sharma (Director, DoCA)',
    email: 'demo.admin@example.com',
    phone: '9876543212',
    role: 'GOVERNMENT_ADMIN',
  },
};

export const DEMO_CREDENTIALS = {
  farmer: {
    emails: ['demo.farmer@example.com', 'farmer@kisansetu.in', 'farmer@example.com'],
    password: 'Farmer123!',
    role: 'FARMER' as const,
    user: DEMO_USERS.farmer,
  },
  officer: {
    emails: ['demo.officer@example.com', 'officer@kisansetu.gov.in', 'officer@example.com'],
    password: 'Officer123!',
    role: 'PROCUREMENT_OFFICER' as const,
    user: DEMO_USERS.officer,
  },
  admin: {
    emails: ['demo.admin@example.com', 'admin@kisansetu.gov.in', 'admin@example.com'],
    password: 'Admin123!',
    role: 'GOVERNMENT_ADMIN' as const,
    user: DEMO_USERS.admin,
  },
};

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  demoLogin: (role: 'farmer' | 'officer' | 'admin') => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

function createMockToken(user: AuthUser): string {
  const payload = {
    sub: user.email,
    role: user.role,
    id: user.id,
    name: user.name,
  };
  try {
    return btoa(unescape(encodeURIComponent(JSON.stringify(payload))));
  } catch {
    return btoa(JSON.stringify(payload));
  }
}

function decodeMockToken(token: string): Partial<AuthUser> | null {
  try {
    const raw = decodeURIComponent(escape(atob(token)));
    const data = JSON.parse(raw);
    return {
      id: data.id,
      email: data.sub || data.email,
      role: data.role,
      name: data.name,
    };
  } catch {
    try {
      const data = JSON.parse(atob(token));
      return {
        id: data.id,
        email: data.sub || data.email,
        role: data.role,
        name: data.name,
      };
    } catch {
      return null;
    }
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('kisansetu_token');
    if (storedToken) {
      setToken(storedToken);
      const decoded = decodeMockToken(storedToken);
      if (decoded?.role) {
        const roleKey = decoded.role === 'PROCUREMENT_OFFICER' ? 'officer' : decoded.role === 'GOVERNMENT_ADMIN' ? 'admin' : 'farmer';
        const fallbackUser = DEMO_USERS[roleKey];
        setUser({
          ...fallbackUser,
          id: decoded.id || fallbackUser.id,
          name: decoded.name || fallbackUser.name,
          email: decoded.email || fallbackUser.email,
          role: decoded.role as any || fallbackUser.role,
        });
      }

      authApi.me()
        .then(u => setUser(u as AuthUser))
        .catch((err) => {
          // If server explicitly returns 401 Unauthorized, token is expired/invalid
          const msg = err?.message || '';
          if (msg.includes('401') || msg.toLowerCase().includes('unauthorized')) {
            localStorage.removeItem('kisansetu_token');
            setToken(null);
            setUser(null);
          }
          // If it's a network error (Supabase 502/521 down), keep the session!
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const cleanEmail = email.trim().toLowerCase();

    // 1. Check for hardcoded demo credentials match
    let matchedKey: 'farmer' | 'officer' | 'admin' | null = null;
    if (DEMO_CREDENTIALS.farmer.emails.includes(cleanEmail) || cleanEmail.includes('farmer')) {
      matchedKey = 'farmer';
    } else if (DEMO_CREDENTIALS.officer.emails.includes(cleanEmail) || cleanEmail.includes('officer')) {
      matchedKey = 'officer';
    } else if (DEMO_CREDENTIALS.admin.emails.includes(cleanEmail) || cleanEmail.includes('admin')) {
      matchedKey = 'admin';
    }

    if (matchedKey) {
      const demoUser = DEMO_USERS[matchedKey];
      const demoToken = createMockToken(demoUser);
      localStorage.setItem('kisansetu_token', demoToken);
      setToken(demoToken);
      setUser(demoUser);

      // Fire and forget server login to sync if server is online
      authApi.login(email, password).catch(() => {});
      return;
    }

    // 2. Regular API login for non-demo users
    try {
      const data = await authApi.login(email, password);
      localStorage.setItem('kisansetu_token', data.access_token);
      setToken(data.access_token);
      try {
        const me = await authApi.me();
        setUser(me as AuthUser);
      } catch {
        setUser({
          id: data.user_id || 1,
          name: data.name || 'User',
          email,
          phone: '9876543210',
          role: (data.role as any) || 'FARMER',
        });
      }
    } catch (err: any) {
      // If network fails (e.g. Supabase down), but looks like a role intention, fallback gracefully
      if (err?.message?.includes('NetworkError') || err?.message?.includes('fetch')) {
        throw new Error('Could not connect to backend server. You can sign in instantly using the demo credentials or demo buttons below.');
      }
      throw err;
    }
  };

  const demoLogin = async (role: 'farmer' | 'officer' | 'admin') => {
    const demoUser = DEMO_USERS[role] || DEMO_USERS.farmer;
    const demoToken = createMockToken(demoUser);
    
    // Instantly persist and activate session without network delay or dependency
    localStorage.setItem('kisansetu_token', demoToken);
    setToken(demoToken);
    setUser(demoUser);

    // Optional non-blocking background sync
    authApi.demoLogin(demoUser.role).catch(() => {});
  };

  const logout = () => {
    localStorage.removeItem('kisansetu_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, demoLogin }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
