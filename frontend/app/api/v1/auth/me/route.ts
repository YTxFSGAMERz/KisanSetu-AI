import { NextResponse } from 'next/server';
import { verifyToken, extractBearerToken } from '@/lib/jwt';
import { db } from '@/lib/db';

export async function GET(req: Request) {
  const authHeader = req.headers.get('authorization');
  const rawToken = extractBearerToken(authHeader);

  if (!rawToken) {
    return NextResponse.json({ detail: 'Not authenticated' }, { status: 401 });
  }

  // Verify the real JWT
  const payload = await verifyToken(rawToken);
  if (!payload) {
    return NextResponse.json({ detail: 'Invalid or expired token' }, { status: 401 });
  }

  // Look up user from store using sub (user ID)
  const userId = Number(payload.sub);
  const users = db.getState().users;
  const user = users.find((u: any) => u.id === userId);

  if (user) {
    return NextResponse.json({
      id: user.id,
      email: user.email,
      phone: user.phone || '9876543210',
      name: user.name || user.full_name,
      role: user.role,
      farmer_id: user.role === 'FARMER' ? user.farmer_id || 1 : undefined,
      centre_id: user.centre_id,
      is_active: user.is_active !== false,
    });
  }

  // Fallback: build response from JWT payload (for demo users not in store)
  return NextResponse.json({
    id: userId,
    email: `demo.${payload.role.toLowerCase().replace('_', '.')}@example.com`,
    phone: '9876543210',
    name: payload.name,
    role: payload.role,
    farmer_id: payload.role === 'FARMER' ? 1 : undefined,
    centre_id: payload.role === 'PROCUREMENT_OFFICER' ? 1 : undefined,
    is_active: true,
  });
}
