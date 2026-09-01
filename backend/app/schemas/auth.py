"""Pydantic schemas for authentication."""
from pydantic import BaseModel, EmailStr, field_validator
from app.models.user import UserRole


class RegisterRequest(BaseModel):
    name: str
    phone: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.FARMER

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        name = v.strip()
        if len(name) < 2 or len(name) > 100:
            raise ValueError("Name must be between 2 and 100 characters")
        return name

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 128:
            raise ValueError("Password cannot exceed 128 characters")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        digits = v.replace("+91", "").replace("-", "").replace(" ", "")
        if not digits.isdigit() or len(digits) != 10:
            raise ValueError("Phone must be a 10-digit Indian mobile number")
        return digits


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class DemoLoginRequest(BaseModel):
    role: UserRole


class OTPSendRequest(BaseModel):
    phone: str


class OTPVerifyRequest(BaseModel):
    phone: str
    otp: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: UserRole
    name: str


class UserResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}
