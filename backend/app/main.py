"""
KisanSetu AI — FastAPI Backend Entry Point
Smart Procurement Management Platform | SIH Problem 26032
Hardened with Security Headers, CORS isolation, and Global Exception Protection.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.api import api_router
from app.core.config import settings
from app.database.session import engine, Base


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds enterprise security headers to all responses."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"✅ KisanSetu AI backend running on http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    print(f"📖 API Documentation: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}/docs")
    yield
    # Shutdown
    await engine.dispose()
    print("🛑 KisanSetu AI backend shutting down")


app = FastAPI(
    title="KisanSetu AI — Secure Procurement API",
    description=(
        "## 🌾 KisanSetu AI — Smart Procurement Management Platform\n\n"
        "**SIH Problem Statement 26032** | Ministry of Consumer Affairs, Food & Public Distribution\n\n"
        "### Enterprise Security Features\n"
        "- Zero hardcoded keys or credentials\n"
        "- Strict Role-Based Access Control (RBAC) & IDOR Protection\n"
        "- JWT Authentication with Argon2/Bcrypt hashing\n"
        "- Real-time authenticated WebSocket queue feeds\n"
        "- OWASP-hardened security response headers\n"
    ),
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG or settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.DEBUG or settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# Enterprise Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# CORS — strict origin matching from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

# Global Safe Exception Handler (prevents stack traces / DB internal leaks)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    if settings.DEBUG:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "debug_error": str(exc)},
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please contact system administrator."},
    )


# Register all API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "KisanSetu AI Secure Backend",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "problem_statement": "SIH 26032",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "KisanSetu AI"}
