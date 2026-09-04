import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    id: 1,
    user_id: 1,
    farmer_registration_number: 'FRN-HR-2026-0042',
    aadhaar_last_four: '9012',
    land_size_acres: 12.5,
    preferred_language: 'hi',
    village: 'Kachhwa',
    district: 'Karnal',
    state: 'Haryana',
    bank_account_verified: true,
  });
}

export async function PUT(req: Request) {
  const body = await req.json().catch(() => ({}));
  return NextResponse.json({
    id: 1,
    user_id: 1,
    farmer_registration_number: 'FRN-HR-2026-0042',
    aadhaar_last_four: '9012',
    land_size_acres: 12.5,
    preferred_language: 'hi',
    village: 'Kachhwa',
    district: 'Karnal',
    state: 'Haryana',
    bank_account_verified: true,
    ...body,
  });
}
