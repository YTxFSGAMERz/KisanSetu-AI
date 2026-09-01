import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const url = new URL(req.url);
    const roleParam = url.searchParams.get('role')?.toUpperCase() || 'FARMER';
    
    let user;
    if (roleParam.includes('OFFICER')) {
      user = {
        id: 2,
        email: 'officer@kisansetu.gov.in',
        phone: '9876543211',
        name: 'Anil Kumar (Mandi Officer)',
        full_name: 'Anil Kumar (Mandi Officer)',
        role: 'PROCUREMENT_OFFICER',
        centre_id: 1,
        is_active: true,
      };
    } else if (roleParam.includes('ADMIN')) {
      user = {
        id: 3,
        email: 'admin@kisansetu.gov.in',
        phone: '9876543212',
        name: 'Dr. Ramesh Sharma (Director, DoCA)',
        full_name: 'Dr. Ramesh Sharma (Director, DoCA)',
        role: 'GOVERNMENT_ADMIN',
        is_active: true,
      };
    } else {
      user = {
        id: 1,
        email: 'farmer@kisansetu.in',
        phone: '9876543210',
        name: 'Rajesh Verma (Kisan)',
        full_name: 'Rajesh Verma (Kisan)',
        role: 'FARMER',
        farmer_id: 1,
        is_active: true,
      };
    }

    const token = Buffer.from(JSON.stringify({ sub: user.email, role: user.role, id: user.id })).toString('base64');

    return NextResponse.json({
      access_token: token,
      token_type: 'bearer',
      user,
    });
  } catch (error: any) {
    return NextResponse.json({ detail: error.message || 'Login failed' }, { status: 500 });
  }
}
