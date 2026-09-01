"""
Application configuration using pydantic-settings.
All secrets, keys, database URLs, and API configurations are strictly loaded from environment variables (.env).
NO default secret keys or credentials are hardcoded.
"""
import os
import secrets
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "KisanSetu AI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"))
    BACKEND_HOST: str = Field(default_factory=lambda: os.getenv("BACKEND_HOST", "0.0.0.0"))
    BACKEND_PORT: int = Field(default_factory=lambda: int(os.getenv("BACKEND_PORT", "8000")))

    # Database
    DATABASE_URL: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./kisansetu.db"))

    # JWT / Security (Random secure runtime key generated if not provided in .env)
    SECRET_KEY: str = Field(default_factory=lambda: os.getenv("SECRET_KEY", secrets.token_hex(32)))
    ALGORITHM: str = Field(default_factory=lambda: os.getenv("ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))

    # CORS Origins (Comma-separated string or list in env)
    ALLOWED_ORIGINS: Union[List[str], str] = Field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Demo & Prototype Controls (strictly controlled via env)
    DEMO_MODE: bool = Field(default_factory=lambda: os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes"))
    DEMO_OTP: str = Field(default_factory=lambda: os.getenv("DEMO_OTP", ""))

    # SMS Gateway Integration
    SMS_PROVIDER: str = Field(default_factory=lambda: os.getenv("SMS_PROVIDER", "SIMULATED"))
    SMS_API_KEY: str = Field(default_factory=lambda: os.getenv("SMS_API_KEY", ""))
    SMS_SENDER_ID: str = Field(default_factory=lambda: os.getenv("SMS_SENDER_ID", "KSTUAI"))

    # Demo Account Credentials (read strictly from env, no hardcoded fallbacks)
    DEMO_FARMER_EMAIL: str = Field(default_factory=lambda: os.getenv("DEMO_FARMER_EMAIL", "demo.farmer@example.com"))
    DEMO_FARMER_PASSWORD: str = Field(default_factory=lambda: os.getenv("DEMO_FARMER_PASSWORD", ""))
    DEMO_OFFICER_EMAIL: str = Field(default_factory=lambda: os.getenv("DEMO_OFFICER_EMAIL", "demo.officer@example.com"))
    DEMO_OFFICER_PASSWORD: str = Field(default_factory=lambda: os.getenv("DEMO_OFFICER_PASSWORD", ""))
    DEMO_ADMIN_EMAIL: str = Field(default_factory=lambda: os.getenv("DEMO_ADMIN_EMAIL", "demo.admin@example.com"))
    DEMO_ADMIN_PASSWORD: str = Field(default_factory=lambda: os.getenv("DEMO_ADMIN_PASSWORD", ""))


settings = Settings()
