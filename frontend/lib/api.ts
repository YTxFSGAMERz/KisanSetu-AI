// Base URL is set via NEXT_PUBLIC_API_URL env variable (defaults to relative /api/v1 for Vercel)
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';
export const API_URL = API_BASE ? `${API_BASE}/api/v1` : '/api/v1';
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || (typeof window !== 'undefined' ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}` : 'ws://localhost:8000');

// ─── HTTP helpers ────────────────────────────────────────────────────────────

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('kisansetu_token');
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  authenticated = true
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (authenticated) {
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  const primaryUrl = `${API_URL}${path}`;
  try {
    const response = await fetch(primaryUrl, {
      ...options,
      headers,
    });

    if (!response.ok) {
      // If backend threw 502/521/500 and API_BASE was configured, trigger fallback
      if (API_BASE && response.status >= 500) {
        throw new Error(`SERVER_ERROR_${response.status}`);
      }
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return response.json();
  } catch (err: any) {
    // If backend is offline, network failed, or Supabase returned 502/521, fallback to local Next.js API routes
    if (API_BASE && (err instanceof TypeError || err.message?.includes('NetworkError') || err.message?.includes('fetch') || err.message?.startsWith('SERVER_ERROR_'))) {
      try {
        const fallbackRes = await fetch(`/api/v1${path}`, {
          ...options,
          headers,
        });
        if (fallbackRes.ok) {
          return fallbackRes.json();
        }
      } catch {
        // Fallback fetch also failed
      }
    }

    throw err;
  }
}

// ─── Auth API ────────────────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    request<{
      access_token: string;
      user_id: number;
      role: string;
      name: string;
    }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }, false),

  demoLogin: (role: string) =>
    request<{
      access_token: string;
      user_id: number;
      role: string;
      name: string;
    }>('/auth/demo-login', {
      method: 'POST',
      body: JSON.stringify({ role }),
    }, false),

  register: (data: {
    name: string;
    phone: string;
    email: string;
    password: string;
    role?: string;
  }) =>
    request<{ access_token: string; user_id: number; role: string; name: string }>(
      '/auth/register',
      { method: 'POST', body: JSON.stringify(data) },
      false
    ),

  sendOtp: (phone: string) =>
    request<{ message: string; demo_otp: string }>(
      '/auth/otp/send',
      { method: 'POST', body: JSON.stringify({ phone }) },
      false
    ),

  verifyOtp: (phone: string, otp: string) =>
    request<{ access_token: string; user_id: number; role: string; name: string }>(
      '/auth/otp/verify',
      { method: 'POST', body: JSON.stringify({ phone, otp }) },
      false
    ),

  me: () => request<{ id: number; name: string; email: string; role: string; phone: string }>('/auth/me'),
};

// ─── Centres API ─────────────────────────────────────────────────────────────

export const centresApi = {
  list: (state?: string) =>
    request<any[]>(`/centres${state ? `?state=${state}` : ''}`),
  get: (id: number) => request<any>(`/centres/${id}`),
  availability: (id: number, date?: string) =>
    request<any>(`/centres/${id}/availability${date ? `?date=${date}` : ''}`),
  crops: () => request<any[]>('/centres/crops'),
};

// ─── Slots API ───────────────────────────────────────────────────────────────

export const slotsApi = {
  list: (centreId?: number, date?: string) => {
    const params = new URLSearchParams();
    if (centreId) params.set('centre_id', String(centreId));
    if (date) params.set('date', date);
    return request<any[]>(`/slots?${params.toString()}`);
  },
  recommendations: (centreId: number, date?: string, cropId?: number) => {
    const params = new URLSearchParams({ centre_id: String(centreId) });
    if (date) params.set('date', date);
    if (cropId) params.set('crop_id', String(cropId));
    return request<any>(`/slots/recommendations?${params.toString()}`);
  },
};

// ─── Farmer API ──────────────────────────────────────────────────────────────

export const farmerApi = {
  me: () => request<any>('/farmers/me'),
  update: (data: any) => request<any>('/farmers/me', { method: 'PUT', body: JSON.stringify(data) }),
  dashboard: () => request<any>('/farmers/dashboard'),
};

// ─── Bookings API ────────────────────────────────────────────────────────────

export const bookingsApi = {
  create: (data: {
    centre_id: number;
    slot_id: number;
    crop_id: number;
    expected_quantity: number;
    notes?: string;
  }) => request<any>('/bookings', { method: 'POST', body: JSON.stringify(data) }),
  my: () => request<any[]>('/bookings/my'),
  get: (id: number) => request<any>(`/bookings/${id}`),
  cancel: (id: number) => request<any>(`/bookings/${id}/cancel`, { method: 'PUT' }),
};

// ─── Queue API ───────────────────────────────────────────────────────────────

export const queueApi = {
  status: (centreId: number) =>
    request<any>(`/queue/status?centre_id=${centreId}`),
  getByBooking: (bookingId: number) =>
    request<any>(`/queue/${bookingId}`),
  callNext: (centreId: number) =>
    request<any>(`/queue/call-next?centre_id=${centreId}`, { method: 'POST' }),
  start: (tokenId: number) =>
    request<any>(`/queue/${tokenId}/start`, { method: 'POST' }),
  complete: (tokenId: number) =>
    request<any>(`/queue/${tokenId}/complete`, { method: 'POST' }),
  skip: (tokenId: number) =>
    request<any>(`/queue/${tokenId}/skip`, { method: 'POST' }),
  noShow: (tokenId: number) =>
    request<any>(`/queue/${tokenId}/no-show`, { method: 'POST' }),
};

// ─── Procurement API ─────────────────────────────────────────────────────────

export const procurementsApi = {
  create: (data: any) =>
    request<any>('/procurements', { method: 'POST', body: JSON.stringify(data) }),
  my: () => request<any[]>('/procurements/my'),
  get: (id: number) => request<any>(`/procurements/${id}`),
  update: (id: number, data: any) =>
    request<any>(`/procurements/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
};

// ─── Payment API ─────────────────────────────────────────────────────────────

export const paymentsApi = {
  my: () => request<any[]>('/payments/my'),
  get: (id: number) => request<any>(`/payments/${id}`),
  process: (id: number) =>
    request<any>(`/payments/${id}/process`, { method: 'POST', body: JSON.stringify({}) }),
};

// ─── Notifications API ───────────────────────────────────────────────────────

export const notificationsApi = {
  list: () => request<any[]>('/notifications'),
  markRead: (ids: number[]) =>
    request<any>('/notifications/read', {
      method: 'POST',
      body: JSON.stringify({ notification_ids: ids }),
    }),
};

// ─── Analytics API ───────────────────────────────────────────────────────────

export const analyticsApi = {
  adminDashboard: () => request<any>('/analytics/admin/dashboard'),
  officerDashboard: (centreId: number) =>
    request<any>(`/analytics/officer/dashboard?centre_id=${centreId}`),
};
