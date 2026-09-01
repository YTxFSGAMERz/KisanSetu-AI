'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { authApi } from '@/lib/api';

interface AuthUser {
  id: number;
  name: string;
  email: string;
  phone: string;
  role: 'FARMER' | 'PROCUREMENT_OFFICER' | 'CENTRE_ADMIN' | 'GOVERNMENT_ADMIN';
}

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  demoLogin: (role: 'farmer' | 'officer' | 'admin') => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('kisansetu_token');
    if (storedToken) {
      setToken(storedToken);
      authApi.me()
        .then(u => setUser(u as AuthUser))
        .catch(() => {
          localStorage.removeItem('kisansetu_token');
          setToken(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const data = await authApi.login(email, password);
    localStorage.setItem('kisansetu_token', data.access_token);
    setToken(data.access_token);
    const me = await authApi.me();
    setUser(me as AuthUser);
  };

  const demoLogin = async (role: 'farmer' | 'officer' | 'admin') => {
    const roleMapping: Record<string, string> = {
      farmer: 'FARMER',
      officer: 'PROCUREMENT_OFFICER',
      admin: 'GOVERNMENT_ADMIN',
    };
    const targetRole = roleMapping[role] || 'FARMER';
    const data = await authApi.demoLogin(targetRole);
    localStorage.setItem('kisansetu_token', data.access_token);
    setToken(data.access_token);
    const me = await authApi.me();
    setUser(me as AuthUser);
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
