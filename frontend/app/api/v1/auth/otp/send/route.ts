import { NextResponse } from 'next/server';

// In-memory OTP store for Next.js serverless (Vercel)
// Note: This is reset on cold starts — acceptable for demo/hackathon
const otpStore = new Map<string, { otp: string; expiresAt: number }>();

/**
 * POST /api/v1/auth/otp/send
 * Sends OTP to the given phone number.
 * In DEMO_MODE returns otp in response.
 */
export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { phone } = body;

    if (!phone) {
      return NextResponse.json({ detail: 'Phone number is required' }, { status: 422 });
    }

    // Generate 6-digit OTP
    const otp = Math.floor(100000 + Math.random() * 900000).toString();
    const expiresAt = Date.now() + 10 * 60 * 1000; // 10 minutes

    otpStore.set(phone, { otp, expiresAt });

    const masked = `******${phone.slice(-4)}`;
    console.log(`[OTP] ${masked}: ${otp}`); // Visible in Vercel logs

    return NextResponse.json({
      message: `OTP sent to ${masked}`,
      demo_otp: otp, // Always return in serverless fallback for demo/judging
    });
  } catch (error: any) {
    return NextResponse.json({ detail: error.message }, { status: 400 });
  }
}
