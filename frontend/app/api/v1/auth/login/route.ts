import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { signToken } from '@/lib/jwt';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { email, password } = body;

    // Look up user in the DB store
    const users = db.getState().users;
    const user = users.find((u: any) =>
      u.email?.toLowerCase() === email?.toLowerCase()
    );

    if (!user) {
      return NextResponse.json({ detail: 'Invalid email or password' }, { status: 401 });
    }

    // In the serverless fallback, passwords are stored as plain text in seed.json
    // In production, this should use bcrypt — but the real backend handles that
    if (user.password && password && user.password !== password) {
      return NextResponse.json({ detail: 'Invalid email or password' }, { status: 401 });
    }

    const token = await signToken({
      sub: String(user.id),
      role: user.role,
      name: user.name || user.full_name,
    });

    return NextResponse.json({
      access_token: token,
      token_type: 'bearer',
      user_id: user.id,
      role: user.role,
      name: user.name || user.full_name,
    });
  } catch (error: any) {
    return NextResponse.json({ detail: error.message || 'Login failed' }, { status: 400 });
  }
}
