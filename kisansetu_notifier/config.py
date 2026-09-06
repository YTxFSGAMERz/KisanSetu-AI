"""
KisanSetu Notifier — Zero-config auto-detection.

Priority order for settings:
  1. kisansetu_notifier/notifier.env  (optional override)
  2. Project root .env                (auto-detected — same file backend uses)
  3. Sensible defaults

This means running 'python main.py' from the project root with no
extra configuration will just work — it reads the same .env the backend uses.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# ── Locate project root ────────────────────────────────────────────────────────
# This file lives at <root>/kisansetu_notifier/config.py
_THIS_DIR   = Path(__file__).parent                  # kisansetu_notifier/
_PROJECT_ROOT = _THIS_DIR.parent                     # project root

# ── Load env files (notifier.env overrides root .env) ─────────────────────────
_root_env     = _PROJECT_ROOT / ".env"
_notifier_env = _THIS_DIR / "notifier.env"

if _root_env.exists():
    load_dotenv(dotenv_path=_root_env, override=False)   # load root first

if _notifier_env.exists():
    load_dotenv(dotenv_path=_notifier_env, override=True) # notifier.env wins


def _build_api_url() -> str:
    """Derive API URL from BACKEND_HOST / BACKEND_PORT (same keys the backend uses)."""
    host = os.getenv("BACKEND_HOST", "127.0.0.1")
    # 0.0.0.0 means "bind all interfaces" — connect as localhost from same machine
    if host in ("0.0.0.0", ""):
        host = "127.0.0.1"
    port = os.getenv("BACKEND_PORT", "8000")
    return f"http://{host}:{port}"


def _build_ws_url() -> str:
    host = os.getenv("BACKEND_HOST", "127.0.0.1")
    if host in ("0.0.0.0", ""):
        host = "127.0.0.1"
    port = os.getenv("BACKEND_PORT", "8000")
    return f"ws://{host}:{port}"


class NotifierConfig:
    # ── Connection ─────────────────────────────────────────────────────────────
    api_url: str = os.getenv("KISANSETU_API_URL") or _build_api_url()
    ws_url:  str = os.getenv("KISANSETU_WS_URL")  or _build_ws_url()

    # ── Auto-login: prefer notifier-specific creds, fall back to DEMO_ADMIN ───
    # The demo admin account is seeded automatically during first run, so this
    # works out-of-the-box with zero manual configuration.
    email:    str = (
        os.getenv("KISANSETU_EMAIL") or
        os.getenv("DEMO_ADMIN_EMAIL", "demo.admin@example.com")
    )
    password: str = (
        os.getenv("KISANSETU_PASSWORD") or
        os.getenv("DEMO_ADMIN_PASSWORD", "")
    )

    # ── User ID: 0 means "auto-fetch from /auth/me after login" ───────────────
    user_id: int = int(os.getenv("KISANSETU_USER_ID", "0") or "0")

    # ── Popup display duration ─────────────────────────────────────────────────
    popup_duration: int = int(os.getenv("POPUP_DURATION_SECONDS", "8"))

    # ── Which events trigger popups ────────────────────────────────────────────
    _raw_events: str = os.getenv(
        "NOTIFY_EVENTS",
        "FARMER_CALLED,BOOKING_CONFIRMED,PAYMENT_UPDATED,NOTIFICATION",
    )
    notify_events: set = set(e.strip() for e in _raw_events.split(",") if e.strip())


config = NotifierConfig()
