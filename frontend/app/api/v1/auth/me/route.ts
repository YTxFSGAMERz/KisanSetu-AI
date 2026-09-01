import { NextResponse } from 'next/server';

export async function GET(req: Request) {
  const authHeader = req.headers.get('authorization');
  if (!authHeader) {
    return NextResponse.json({ detail: 'Not authenticated' }, { status: 401 });
  }

  try {
    const token = authHeader.replace('Bearer ', '');
    const decoded = JSON.parse(Buffer.from(token, 'base64').toString());
    
    const role = decoded.role || 'FARMER';
    const fullName = role === 'PROCUREMENT_OFFICER' || role === 'OFFICER'
      ? 'Anil Kumar (Mandi Officer)' 
      : role === 'GOVERNMENT_ADMIN' || role === 'ADMIN'
      ? 'Dr. Ramesh Sharma (Director, DoCA)' 
      : 'Rajesh Verma (Kisan)';

    return NextResponse.json({
      id: decoded.id || 1,
      email: decoded.sub || 'farmer@kisansetu.in',
      phone: '9876543210',
      name: fullName,
      full_name: fullName,
      role: role === 'OFFICER' ? 'PROCUREMENT_OFFICER' : role === 'ADMIN' ? 'GOVERNMENT_ADMIN' : role,
      farmer_id: role === 'FARMER' ? 1 : undefined,
      centre_id: role === 'PROCUREMENT_OFFICER' || role === 'OFFICER' ? 1 : undefined,
      is_active: true,
    });
  } catch {
    return NextResponse.json({
      id: 1,
      email: 'farmer@kisansetu.in',
      phone: '9876543210',
      name: 'Rajesh Verma (Kisan)',
      full_name: 'Rajesh Verma (Kisan)',
      role: 'FARMER',
      farmer_id: 1,
      is_active: true,
    });
  }
}
