"""
KisanSetu Notifier — Entry Point.

Starts the system tray icon and the WebSocket client background thread.
The Qt event loop runs on the main thread; the WS client runs in asyncio
on a daemon thread. Communication is via Qt signals (thread-safe).

Usage:
    python main.py

Requirements:
    pip install -r requirements.txt
    Fill in kisansetu_notifier/notifier.env with your credentials.
"""
import asyncio
import logging
import sys
import threading
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtCore import Qt

import pystray
from PIL import Image, ImageDraw

from config import config
from popup import show_notification, popup_signals
from ws_client import run_ws_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("kisansetu-notifier")


# ─── Tray Icon Generation ─────────────────────────────────────────────────────

def _make_tray_icon(size: int = 64) -> Image.Image:
    """
    Generate a simple KisanSetu tray icon (green circle with 'K').
    If assets/icon.png exists, use that instead.
    """
    icon_path = Path(__file__).parent / "assets" / "icon.png"
    if icon_path.exists():
        return Image.open(icon_path).resize((size, size))

    # Fallback: draw a green circle with white 'K'
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2, 2, size - 2, size - 2], fill=(46, 125, 50, 255))
    # Draw 'K' text in the center
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("arial.ttf", int(size * 0.5))
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "K", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - tw) / 2, (size - th) / 2 - 2),
        "K", fill=(255, 255, 255, 255), font=font
    )
    return img


# ─── Event Handler ────────────────────────────────────────────────────────────

def _build_popup_content(event_type: str, data: dict) -> tuple[str, str]:
    """Extract human-readable title + message from WS event data."""
    if event_type == "FARMER_CALLED":
        token = data.get("token_number", "?")
        msg = data.get("message", f"Token {token} has been called. Please go to the counter!")
        return f"🔔 Token {token} Called!", msg

    if event_type == "BOOKING_CONFIRMED":
        bn = data.get("booking_number", "")
        centre = data.get("centre_name", "")
        return "✅ Booking Confirmed", f"Booking {bn} confirmed at {centre}."

    if event_type == "PAYMENT_UPDATED":
        amount = data.get("amount", "")
        ref = data.get("txn_ref", "")
        return "💰 Payment Update", f"₹{amount} transferred. Ref: {ref}"

    if event_type == "QUEUE_UPDATED":
        waiting = data.get("waiting", "?")
        current = data.get("current_token", "—")
        return "📋 Queue Update", f"Waiting: {waiting} | Current token: {current}"

    # Generic NOTIFICATION event
    title = data.get("title", "KisanSetu Notification")
    message = data.get("message", str(data))
    return title, message


def _on_ws_event(event_type: str, data: dict):
    """Called from the asyncio thread — emit Qt signal to show popup on main thread."""
    title, message = _build_popup_content(event_type, data)
    log.info("[EVENT] %s → %s", event_type, title)
    # Thread-safe: Qt signal will be handled on the main Qt thread
    popup_signals.show.emit(event_type, title, message)


# ─── WebSocket Thread ─────────────────────────────────────────────────────────

_ws_loop: asyncio.AbstractEventLoop | None = None


def _start_ws_thread():
    """Run the async WS client in a background daemon thread."""
    global _ws_loop
    _ws_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_ws_loop)
    _ws_loop.run_until_complete(run_ws_client(_on_ws_event))


# ─── System Tray (pystray) ────────────────────────────────────────────────────

def _build_tray_menu(app: QApplication) -> pystray.Menu:
    def on_open(_icon, _item):
        import webbrowser
        webbrowser.open(f"{config.api_url}")

    def on_reconnect(_icon, _item):
        log.info("[TRAY] Reconnect requested — restarting WS thread")
        t = threading.Thread(target=_start_ws_thread, daemon=True)
        t.start()

    def on_quit(_icon, _item):
        log.info("[TRAY] Quitting")
        _icon.stop()
        app.quit()

    return pystray.Menu(
        pystray.MenuItem("Open KisanSetu", on_open, default=True),
        pystray.MenuItem("Reconnect", on_reconnect),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_quit),
    )


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    log.info("🌾 KisanSetu Notifier starting...")
    log.info("   API: %s | User ID: %d", config.api_url, config.user_id)
    log.info("   Events: %s", ", ".join(sorted(config.notify_events)))

    # Qt application (headless — no main window)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("KisanSetu Notifier")

    # Connect the thread-safe signal to the popup creator (runs on main thread)
    popup_signals.show.connect(show_notification)

    # Start WebSocket listener in background thread
    ws_thread = threading.Thread(target=_start_ws_thread, daemon=True, name="KisanSetu-WS")
    ws_thread.start()
    log.info("[WS] Background thread started")

    # Build pystray tray icon (runs its own thread internally)
    tray_image = _make_tray_icon(64)
    tray_menu = _build_tray_menu(app)
    tray_icon = pystray.Icon(
        name="KisanSetu Notifier",
        icon=tray_image,
        title="KisanSetu Notifier — Connected",
        menu=tray_menu,
    )

    # Run pystray in a daemon thread (it has its own loop)
    tray_thread = threading.Thread(target=tray_icon.run, daemon=True, name="KisanSetu-Tray")
    tray_thread.start()
    log.info("[TRAY] System tray icon started")

    # Qt event loop — blocks until app.quit() is called
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
