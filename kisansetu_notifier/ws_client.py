"""
KisanSetu Notifier — WebSocket Client.

Authenticates against the KisanSetu backend, then maintains a persistent
WebSocket connection to /api/v1/ws/user/{user_id}.

Auto-detects user_id by calling /api/v1/auth/me after login — no manual
configuration needed.

Reconnects automatically with exponential backoff on any disconnect.
The on_event callback is called (thread-safely via Qt signal) for each
JSON message received from the server.
"""
import asyncio
import json
import logging
from typing import Callable

import httpx
import websockets
from websockets.exceptions import ConnectionClosed

from config import config

log = logging.getLogger(__name__)

_MIN_BACKOFF = 1.0    # seconds
_MAX_BACKOFF = 30.0   # seconds


async def _login() -> tuple[str, int]:
    """
    POST /api/v1/auth/login and return (jwt_token, user_id).
    user_id is fetched from /api/v1/auth/me — fully automatic, no config needed.
    Raises on failure.
    """
    login_url = f"{config.api_url}/api/v1/auth/login"

    async with httpx.AsyncClient(timeout=10.0) as client:
        # ── Step 1: get JWT token ─────────────────────────────────────────────
        resp = await client.post(
            login_url,
            data={
                "username": config.email,
                "password": config.password,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        token = resp.json().get("access_token", "")
        if not token:
            raise ValueError("Login response contained no access_token")

        # ── Step 2: resolve user_id ───────────────────────────────────────────
        user_id = config.user_id  # may be 0 (auto-detect)
        if user_id == 0:
            me_resp = await client.get(
                f"{config.api_url}/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            me_resp.raise_for_status()
            user_id = me_resp.json().get("id", 0)
            if not user_id:
                raise ValueError("/auth/me did not return a valid user id")
            log.info("[WS] Auto-detected user_id = %d for %s", user_id, config.email)

    log.info("[WS] Logged in as %s (user_id=%d)", config.email, user_id)
    return token, user_id


async def run_ws_client(on_event: Callable[[str, dict], None]) -> None:
    """
    Maintains a persistent, authenticated WebSocket connection.
    Calls on_event(event_type: str, data: dict) for each relevant message.
    Auto-reconnects with exponential backoff.
    """
    backoff = _MIN_BACKOFF

    while True:
        try:
            token, user_id = await _login()
            ws_url = (
                f"{config.ws_url}/api/v1/ws/user/{user_id}"
                f"?token={token}"
            )
            log.info("[WS] Connecting to %s", ws_url)

            async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as ws:
                log.info("[WS] ✅ Connected — listening for KisanSetu events")
                backoff = _MIN_BACKOFF  # reset on successful connect

                async for raw in ws:
                    try:
                        payload = json.loads(raw)
                        event_type = payload.get("event", "")
                        data = payload.get("data", {})

                        if event_type in config.notify_events:
                            log.debug("[WS] Event: %s | %s", event_type, data)
                            on_event(event_type, data)
                        else:
                            log.debug("[WS] Ignored event: %s", event_type)

                    except json.JSONDecodeError:
                        log.warning("[WS] Non-JSON message: %s", raw[:100])

        except (ConnectionClosed, websockets.exceptions.WebSocketException) as exc:
            log.warning("[WS] Disconnected: %s — reconnecting in %.0fs", exc, backoff)
        except httpx.HTTPStatusError as exc:
            log.error(
                "[WS] Auth failed (HTTP %d) — check credentials in .env — retrying in %.0fs",
                exc.response.status_code, backoff
            )
        except Exception as exc:
            log.error("[WS] Error: %s — retrying in %.0fs", exc, backoff)

        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, _MAX_BACKOFF)
