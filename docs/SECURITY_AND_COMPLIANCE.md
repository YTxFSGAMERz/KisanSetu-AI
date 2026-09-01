# KisanSetu AI — Security, Governance & Compliance Architecture

**Classification**: High-Security Government Agro-Tech Platform  
**Compliance Target**: National Cybersecurity Policy, Aadhaar Data Vault Principles, OWASP Top 10 API Security  

---

## 1. Zero-Credential Exposure Architecture

KisanSetu AI is engineered with a strict **Zero-Hardcoded Secrets Policy**:

1. **Client-Side Bundles**:
   - Zero API keys, passwords, database URLs, or service credentials exist in client-side Next.js code or JavaScript bundles.
   - Demo logins use server-side token minting (`/auth/demo-login`) strictly gated by `DEMO_MODE=true` in `.env`.
   - In production (`DEMO_MODE=false`), the demo endpoint returns `403 Forbidden` and is unreachable.

2. **Environment Isolation**:
   - All backend configuration is loaded strictly at runtime through `pydantic-settings` from `.env`.
   - If `SECRET_KEY` is omitted, the system generates a cryptographically random 32-byte secret (`secrets.token_hex(32)`) in memory.

3. **Repository Defense**:
   - Comprehensive root and nested `.gitignore` configurations prevent tracking of `.env`, `.env.*`, `*.db`, `*.sqlite*`, `*.pem`, `*.key`, and `credentials.json`.

---

## 2. Insecure Direct Object Reference (IDOR) Shield

Every data endpoint that returns or mutates farmer records enforces strict ownership validation:

```python
# IDOR Guard Example (bookings.py, procurements.py, payments.py, queue.py)
if current_user.role == UserRole.FARMER:
    farmer = await db.scalar(select(Farmer).where(Farmer.user_id == current_user.id))
    if not booking or not farmer or booking.farmer_id != farmer.id:
        raise HTTPException(
            status_code=403, 
            detail="Access denied: You cannot view or modify records belonging to other farmers."
        )
```

| Route | IDOR Mitigation |
|---|---|
| `GET /bookings/{id}` | Verifies `booking.farmer_id == current_user.farmer.id` |
| `GET /procurements/{id}` | Verifies ownership through `procurement.booking.farmer_id` |
| `GET /payments/{id}` | Verifies ownership through `payment.procurement.booking.farmer_id` |
| `GET /queue/{booking_id}` | Verifies booking ownership before revealing queue token position |
| `WS /ws/user/{user_id}` | Verifies JWT `sub == user_id` before opening private event socket |

---

## 3. Database Row Level Security (RLS) Policies (PostgreSQL / Supabase)

All 10 public schema tables have **Row Level Security enabled (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY;`)**.

```sql
-- Example: Strict Farmer Data Isolation Policy
CREATE POLICY "Farmers can view their own bookings"
    ON public.bookings FOR SELECT
    USING (
        farmer_id IN (
            SELECT id FROM public.farmers 
            WHERE user_id::text = (SELECT auth.uid()::text)
        )
        OR (SELECT auth.role()) = 'service_role'
    );
```

### Table Policy Matrix

| Table | Anonymous Access | Authenticated Farmer | Officer / Admin |
|---|---|---|---|
| `users` | ❌ Blocked | ✅ View own profile only | ✅ View authorized accounts |
| `farmers` | ❌ Blocked | ✅ View own record only | ✅ View centre farmers |
| `procurement_centres` | ✅ Read-only (Active) | ✅ Read-only | ✅ Full access |
| `crops` | ✅ Read-only (Active) | ✅ Read-only | ✅ Full access |
| `slots` | ✅ Read-only (Open) | ✅ Read-only | ✅ Manage capacities |
| `bookings` | ❌ Blocked | ✅ Manage own bookings | ✅ View centre bookings |
| `queue_tokens` | ❌ Blocked | ✅ View own token | ✅ Call & advance queue |
| `procurements` | ❌ Blocked | ✅ View own receipts | ✅ Create & grade |
| `payments` | ❌ Blocked | ✅ View own payments | ✅ Process payments |
| `notifications` | ❌ Blocked | ✅ View & acknowledge own | ❌ Blocked from others |

---

## 4. Enterprise Security Response Headers

The backend applies `SecurityHeadersMiddleware` on every HTTP response:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(self), camera=(), microphone=()
Strict-Transport-Security: max-age=31536000; includeSubDomains (Production)
```

---

## 5. Farmer Data Privacy & Masking

1. **Aadhaar Privacy**:
   - The platform never stores 12-digit Aadhaar numbers in plaintext.
   - Only the last 4 digits (`aadhaar_last4`) are stored for verification against government procurement rosters.

2. **PII Logging Masking**:
   - Phone numbers and sensitive identities in server loggers are masked (`******3421`).
   - Exception handlers catch database internal errors and return generic error IDs to prevent schema enumeration.
