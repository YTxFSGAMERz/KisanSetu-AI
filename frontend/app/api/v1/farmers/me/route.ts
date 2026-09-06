import { NextResponse } from 'next/server';
import { verifyToken, extractBearerToken } from '@/lib/jwt';

// In-memory farmer profile storage for serverless fallback mode
const serverlessFarmerProfiles: Record<number, any> = {};

export async function GET(req: Request) {
  const authHeader = req.headers.get('authorization');
  const token = extractBearerToken(authHeader);
  const payload = token ? await verifyToken(token) : null;
  const userId = payload ? Number(payload.sub) : 1;

  const farmer = serverlessFarmerProfiles[userId] || {
    id: 1,
    user_id: userId,
    farmer_registration_number: 'FRN-HR-2026-0042',
    aadhaar_last_four: '9012',
    land_area_acres: 12.5,
    language: 'hi',
    village: 'Kachhwa',
    district: 'Karnal',
    state: 'Haryana',
    bank_account_number: '********1012',
    bank_ifsc: 'SBIN0001234',
    bank_name: 'State Bank of India',
    has_bank_account: true,
    bank_account_verified: true,
  };

  return NextResponse.json({
    ...farmer,
    id: farmer.id || 1,
    user_id: userId,
  });
}

export async function PUT(req: Request) {
  const authHeader = req.headers.get('authorization');
  const token = extractBearerToken(authHeader);
  const payload = token ? await verifyToken(token) : null;
  const userId = payload ? Number(payload.sub) : 1;

  const body = await req.json().catch(() => ({}));

  const existing = serverlessFarmerProfiles[userId] || {
    id: 1,
    user_id: userId,
    farmer_registration_number: 'FRN-HR-2026-0042',
    aadhaar_last_four: '9012',
    land_area_acres: 12.5,
    language: 'hi',
    village: 'Kachhwa',
    district: 'Karnal',
    state: 'Haryana',
  };

  const updated = {
    ...existing,
    ...body,
    bank_account_number: body.bank_account_number ? `****${String(body.bank_account_number).slice(-4)}` : existing.bank_account_number,
    has_bank_account: Boolean(body.bank_account_number || existing.bank_account_number),
  };

  serverlessFarmerProfiles[userId] = updated;

  return NextResponse.json(updated);
}
