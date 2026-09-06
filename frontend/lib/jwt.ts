/**
 * JWT helpers for Next.js serverless API routes (fallback mode).
 * Uses `jose` — the only JWT library that works in Edge/Serverless without Node crypto.
 *
 * Set JWT_SECRET_KEY in your .env.local (min 32 characters):
 *   JWT_SECRET_KEY=your-super-secret-key-min-32-chars-here
 */
import { SignJWT, jwtVerify } from 'jose';

const SECRET_KEY = process.env.JWT_SECRET_KEY || process.env.NEXTAUTH_SECRET;

function getSecret(): Uint8Array {
  const key = SECRET_KEY;
  if (!key || key.length < 16) {
    console.warn('[JWT] JWT_SECRET_KEY not set or too short — using insecure fallback. Set JWT_SECRET_KEY in .env.local');
    return new TextEncoder().encode('kisansetu_secure_development_secret_key_2026');
  }
  return new TextEncoder().encode(key);
}

export interface JWTPayload {
  sub: string;          // user ID as string
  role: string;         // UserRole
  name: string;
  exp?: number;
  iat?: number;
}

/** Create a signed HS256 JWT that expires in `expiresIn` hours (default 8h). */
export async function signToken(payload: Omit<JWTPayload, 'exp' | 'iat'>, expiresInHours = 8): Promise<string> {
  const secret = getSecret();
  return new SignJWT({ ...payload })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime(`${expiresInHours}h`)
    .sign(secret);
}

/** Verify and decode a JWT. Returns null if invalid or expired. */
export async function verifyToken(token: string): Promise<JWTPayload | null> {
  try {
    const secret = getSecret();
    const { payload } = await jwtVerify(token, secret);
    return payload as unknown as JWTPayload;
  } catch {
    return null;
  }
}

/** Extract bearer token from Authorization header. */
export function extractBearerToken(authHeader: string | null): string | null {
  if (!authHeader) return null;
  const [type, token] = authHeader.split(' ');
  if (type !== 'Bearer' || !token) return null;
  return token;
}
