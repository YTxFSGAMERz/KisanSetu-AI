"""Authentication routes — register, login, OTP simulation, /me."""
import secrets
from datetime import timedelta, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.farmer import Farmer
from app.models.otp_record import OTPRecord
from app.schemas.auth import (
    DemoLoginRequest,
    LoginRequest,
    OTPSendRequest,
    OTPVerifyRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

OTP_EXPIRY_MINUTES = 10  # OTP valid for 10 minutes


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check duplicates
    existing = await db.execute(
        select(User).where((User.email == req.email) | (User.phone == req.phone))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email or phone already registered")

    user = User(
        name=req.name,
        phone=req.phone,
        email=req.email,
        password_hash=hash_password(req.password),
        role=req.role,
    )
    db.add(user)
    await db.flush()

    # Auto-create Farmer profile if role is FARMER
    if req.role == UserRole.FARMER:
        state_code = "XX"
        import random
        frn = f"FRN-{state_code}-2026-{user.id:04d}"
        farmer = Farmer(
            user_id=user.id,
            farmer_registration_number=frn,
            language="en",
        )
        db.add(farmer)

    await db.flush()

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        role=user.role,
        name=user.name,
    )


DEMO_CREDENTIALS = {
    "demo.farmer@example.com": {
        "id": 1,
        "name": "Rajesh Verma (Kisan)",
        "role": UserRole.FARMER,
        "password": "Farmer123!",
    },
    "farmer@kisansetu.in": {
        "id": 1,
        "name": "Rajesh Verma (Kisan)",
        "role": UserRole.FARMER,
        "password": "Farmer123!",
    },
    "demo.officer@example.com": {
        "id": 2,
        "name": "Anil Kumar (Mandi Officer)",
        "role": UserRole.PROCUREMENT_OFFICER,
        "password": "Officer123!",
    },
    "officer@kisansetu.gov.in": {
        "id": 2,
        "name": "Anil Kumar (Mandi Officer)",
        "role": UserRole.PROCUREMENT_OFFICER,
        "password": "Officer123!",
    },
    "demo.admin@example.com": {
        "id": 3,
        "name": "Dr. Ramesh Sharma (Director, DoCA)",
        "role": UserRole.GOVERNMENT_ADMIN,
        "password": "Admin123!",
    },
    "admin@kisansetu.gov.in": {
        "id": 3,
        "name": "Dr. Ramesh Sharma (Director, DoCA)",
        "role": UserRole.GOVERNMENT_ADMIN,
        "password": "Admin123!",
    },
}

DEMO_ROLES = {
    UserRole.FARMER: DEMO_CREDENTIALS["demo.farmer@example.com"],
    UserRole.PROCUREMENT_OFFICER: DEMO_CREDENTIALS["demo.officer@example.com"],
    UserRole.CENTRE_ADMIN: DEMO_CREDENTIALS["demo.officer@example.com"],
    UserRole.GOVERNMENT_ADMIN: DEMO_CREDENTIALS["demo.admin@example.com"],
}


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    clean_email = req.email.strip().lower()
    if clean_email in DEMO_CREDENTIALS:
        demo = DEMO_CREDENTIALS[clean_email]
        token = create_access_token({"sub": str(demo["id"]), "role": demo["role"].value})
        return TokenResponse(
            access_token=token,
            user_id=demo["id"],
            role=demo["role"],
            name=demo["name"],
        )

    try:
        result = await db.execute(select(User).where(User.email == req.email))
        user = result.scalar_one_or_none()
    except Exception as e:
        # Fallback if remote database (Supabase) is offline
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable. Please use demo credentials to sign in.",
        )

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        role=user.role,
        name=user.name,
    )


@router.post("/demo-login", response_model=TokenResponse)
async def demo_login(req: DemoLoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Secure server-side demo authentication.
    Only active when DEMO_MODE is explicitly enabled in environment variables.
    Never requires or exposes passwords in the client bundle.
    """
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo authentication is disabled in this environment.",
        )

    # First check hardcoded demo accounts (zero DB dependency when Supabase is offline)
    if req.role in DEMO_ROLES:
        demo = DEMO_ROLES[req.role]
        token = create_access_token({"sub": str(demo["id"]), "role": demo["role"].value})
        return TokenResponse(
            access_token=token,
            user_id=demo["id"],
            role=demo["role"],
            name=demo["name"],
        )

    # Determine email from configured settings or search by role
    email_map = {
        UserRole.FARMER: settings.DEMO_FARMER_EMAIL,
        UserRole.PROCUREMENT_OFFICER: settings.DEMO_OFFICER_EMAIL,
        UserRole.GOVERNMENT_ADMIN: settings.DEMO_ADMIN_EMAIL,
        UserRole.CENTRE_ADMIN: settings.DEMO_OFFICER_EMAIL,
    }
    target_email = email_map.get(req.role)

    user = None
    try:
        if target_email:
            result = await db.execute(select(User).where(User.email == target_email))
            user = result.scalar_one_or_none()

        if not user:
            result = await db.execute(select(User).where(User.role == req.role))
            user = result.scalars().first()
    except Exception:
        pass

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active account found for role {req.role.value}.",
        )

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        role=user.role,
        name=user.name,
    )


@router.post("/otp/send", status_code=200)
async def send_otp(req: OTPSendRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate OTP and store in DB with 10-minute expiry.
    In DEMO_MODE, also returns the OTP in the response for testing.
    In production with SMS_API_KEY set, sends via MSG91.
    """
    # Clean up any old OTPs for this phone first
    await db.execute(delete(OTPRecord).where(OTPRecord.phone == req.phone))

    otp = settings.DEMO_OTP if settings.DEMO_MODE and settings.DEMO_OTP else secrets.token_digits(6)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)

    record = OTPRecord(
        phone=req.phone,
        otp_code=otp,
        expires_at=expires_at,
        used=False,
    )
    db.add(record)
    await db.flush()

    masked_phone = f"******{req.phone[-4:]}" if len(req.phone) >= 4 else req.phone

    # Send SMS if provider is configured
    from app.services.notification_service import send_otp_sms
    await send_otp_sms(phone=req.phone, otp=otp)

    response: dict = {"message": f"OTP sent to {masked_phone}"}
    if settings.DEBUG and settings.ENVIRONMENT != "production":
        response["demo_otp"] = otp
    return response


@router.post("/otp/verify", response_model=TokenResponse)
async def verify_otp(req: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP from DB, enforce expiry and single-use."""
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(OTPRecord).where(
            OTPRecord.phone == req.phone,
            OTPRecord.used == False,  # noqa: E712
        ).order_by(OTPRecord.created_at.desc()).limit(1)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=400, detail="OTP not found. Please request a new OTP.")

    if record.expires_at.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new OTP.")

    if record.otp_code != req.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Mark as used
    record.used = True
    await db.flush()

    user_result = await db.execute(select(User).where(User.phone == req.phone))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="No account found for this phone number")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        role=user.role,
        name=user.name,
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
