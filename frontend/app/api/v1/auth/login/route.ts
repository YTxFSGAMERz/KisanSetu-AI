import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { email } = body;

    let role = 'FARMER';
    let fullName = 'Rajesh Verma (Kisan)';
    let id = 1;
    let centre_id = undefined;

    if (email?.includes('officer')) {
      role = 'PROCUREMENT_OFFICER';
      fullName = 'Anil Kumar (Mandi Officer)';
      id = 2;
      centre_id = 1;
    } else if (email?.includes('admin')) {
      role = 'GOVERNMENT_ADMIN';
      fullName = 'Dr. Ramesh Sharma (Director, DoCA)';
      id = 3;
    }

    const user = {
      id,
      email: email || 'farmer@kisansetu.in',
      phone: '9876543210',
      name: fullName,
      full_name: fullName,
      role,
      farmer_id: role === 'FARMER' ? 1 : undefined,
      centre_id,
      is_active: true,
    };

    const token = Buffer.from(JSON.stringify({ sub: user.email, role: user.role, id: user.id })).toString('base64');

    return NextResponse.json({
      access_token: token,
      token_type: 'bearer',
      user,
    });
  } catch (error: any) {
    return NextResponse.json({ detail: error.message || 'Login failed' }, { status: 400 });
  }
}
