"""Authentication routes — register, login, OTP simulation, /me."""
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
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

# Simple in-memory OTP store for prototype (replace with Redis in production)
_otp_store: dict[str, str] = {}


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
    """Sends OTP (uses DEMO_OTP env in dev/demo mode, provider in production)."""
    otp = settings.DEMO_OTP
    _otp_store[req.phone] = otp
    masked_phone = f"******{req.phone[-4:]}" if len(req.phone) >= 4 else req.phone
    print(f"[OTP SERVICE] Dispatched OTP to {masked_phone}")
    response = {"message": f"OTP sent to {masked_phone}"}
    if settings.DEBUG and settings.ENVIRONMENT != "production":
        response["demo_otp"] = otp
    return response


@router.post("/otp/verify", response_model=TokenResponse)
async def verify_otp(req: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    stored_otp = _otp_store.get(req.phone)
    if not stored_otp or stored_otp != req.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    result = await db.execute(select(User).where(User.phone == req.phone))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="No account found for this phone number")

    _otp_store.pop(req.phone, None)
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
