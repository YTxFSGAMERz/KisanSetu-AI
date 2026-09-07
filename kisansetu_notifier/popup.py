"""
KisanSetu Notifier — Large Custom Popup Window (>= 1/8 Screen Area).

Renders a large, frameless, always-on-top QWidget at the bottom-right corner
of the screen — completely independent of Windows Action Center / toasts.

Features:
  - Sized to occupy at least 1/8th (~13%) of total screen area on any monitor
  - Big, crisp typography readable from across the room
  - Event-specific highlighted banners (Live Mandi Token Call, Booking, Payment)
  - Direct Action button: "Open KisanSetu Web App"
  - Countdown progress bar with hover-to-pause
  - Stacking: multiple popups slide upward smoothly
  - Thread-safe: call show_notification() from any thread via Qt signal
"""
import sys
import webbrowser
from typing import ClassVar

from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QPoint, pyqtSignal, QObject
)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QPushButton, QGraphicsDropShadowEffect,
    QDesktopWidget
)

try:
    from config import config
except ImportError:
    from kisansetu_notifier.config import config

# ─── Brand Colors ─────────────────────────────────────────────────────────────
_GREEN_DARK  = "#14532D"   # Tailwind green-900
_GREEN_MID   = "#15803D"   # Tailwind green-700
_GREEN_LIGHT = "#16A34A"   # Tailwind green-600
_BG_CARD     = "#FFFFFF"
_BG_SUBTLE   = "#F0FDF4"   # Light emerald tint
_BORDER      = "#86EFAC"   # Soft green border
_TEXT_MAIN   = "#0F172A"   # Slate 900
_TEXT_MUTED  = "#475569"   # Slate 600
_MARGIN      = 20          # Screen margin

# ─── Event Metadata ───────────────────────────────────────────────────────────
_EVENT_META: dict[str, tuple[str, str, str]] = {
    "FARMER_CALLED":     ("📢", "Live Mandi Token Call", "COUNTER 1 • PROCEED IMMEDIATELY"),
    "BOOKING_CONFIRMED": ("✅", "Slot Booking Confirmed", "MANDI PROCUREMENT CONFIRMATION"),
    "PAYMENT_UPDATED":   ("💰", "DBT Payment Update", "DIRECT BENEFIT TRANSFER"),
    "QUEUE_UPDATED":     ("📋", "Queue Status Update", "MANDI LIVE QUEUE"),
    "NOTIFICATION":      ("🌾", "KisanSetu Notification", "OFFICIAL PORTAL ALERT"),
}


def compute_popup_dimensions() -> tuple[int, int]:
    """
    Calculate popup width and height so it occupies at least 1/8th (12.5%) of the screen.
    0.38 width * 0.34 height = 0.1292 (> 1/8 of available screen area).
    On 1920x1080: ~730px × 368px.
    On 1366x768:  ~560px × 300px.
    On 2560x1440: ~970px × 490px.
    """
    screen = QDesktopWidget().availableGeometry()
    w = max(560, int(screen.width() * 0.38))
    h = max(310, int(screen.height() * 0.34))
    return w, h


class _PopupSignals(QObject):
    """Bridge: allows any thread to safely trigger a popup on the Qt main thread."""
    show = pyqtSignal(str, str, str)   # event_type, title, message


popup_signals = _PopupSignals()


class _PopupStack:
    """Tracks currently visible popups so they stack neatly upward."""
    _active: ClassVar[list["NotificationPopup"]] = []

    @classmethod
    def add(cls, popup: "NotificationPopup") -> int:
        cls._active.append(popup)
        return len(cls._active)

    @classmethod
    def remove(cls, popup: "NotificationPopup"):
        if popup in cls._active:
            cls._active.remove(popup)
        for i, p in enumerate(cls._active):
            target_y = _bottom_right_y(i + 1, p.popup_h)
            p._animate_to_y(target_y)

    @classmethod
    def count(cls) -> int:
        return len(cls._active)


def _bottom_right_pos(stack_index: int, w: int, h: int) -> QPoint:
    screen = QDesktopWidget().availableGeometry()
    x = screen.right() - w - _MARGIN
    y = screen.bottom() - (h + _MARGIN) * stack_index
    if y < screen.top() + _MARGIN:
        y = screen.bottom() - (h + _MARGIN)
    return QPoint(x, y)


def _bottom_right_y(stack_index: int, h: int) -> int:
    screen = QDesktopWidget().availableGeometry()
    y = screen.bottom() - (h + _MARGIN) * stack_index
    if y < screen.top() + _MARGIN:
        y = screen.bottom() - (h + _MARGIN)
    return y


class NotificationPopup(QWidget):
    """
    A large custom popup notification window occupying >= 1/8 of the screen.
    Uses Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint.
    """

    def __init__(self, event_type: str, title: str, message: str):
        super().__init__()

        self.popup_w, self.popup_h = compute_popup_dimensions()
        self.is_paused = False

        icon, default_title, badge_tag = _EVENT_META.get(
            event_type, ("🌾", "KisanSetu Notification", "OFFICIAL ALERT")
        )
        display_title = title or default_title

        self.setWindowFlags(
            Qt.Tool |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self.popup_w, self.popup_h)

        # Position at bottom-right, stacked
        stack_idx = _PopupStack.add(self)
        pos = _bottom_right_pos(stack_idx, self.popup_w, self.popup_h)
        self.move(pos)

        self._build_ui(event_type, icon, display_title, badge_tag, message)
        self._start_timer()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self, event_type: str, icon: str, title: str, badge_tag: str, message: str):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)  # Room for shadow
        outer.setSpacing(0)

        # Main Card container
        card = QWidget(self)
        card.setObjectName("card")
        card.setStyleSheet(f"""
            QWidget#card {{
                background-color: {_BG_CARD};
                border: 2px solid {_GREEN_LIGHT};
                border-radius: 16px;
            }}
        """)

        # Soft drop shadow
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(24)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 75))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # ── 1. Top Header Banner ──────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(54)
        header.setStyleSheet(f"""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {_GREEN_DARK}, stop:1 {_GREEN_MID}
            );
            border-top-left-radius: 14px;
            border-top-right-radius: 14px;
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 14, 0)
        h_layout.setSpacing(12)

        # Icon circle
        icon_box = QLabel(icon)
        icon_box.setFixedSize(36, 36)
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setStyleSheet("""
            background: rgba(255, 255, 255, 0.22);
            border-radius: 18px;
            font-size: 20px;
        """)

        # Titles
        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(1)
        title_vbox.setAlignment(Qt.AlignVCenter)

        badge_lbl = QLabel(badge_tag)
        badge_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.75); font-size: 10px; font-weight: 700; letter-spacing: 1px;")

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #FFFFFF; font-weight: 800; font-size: 15px;")
        title_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))

        title_vbox.addWidget(badge_lbl)
        title_vbox.addWidget(title_lbl)

        # App brand tag
        brand_lbl = QLabel("🌾 KisanSetu AI")
        brand_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.85); font-size: 11px; font-weight: 600;")

        # Close '✕' button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                border-radius: 14px;
                border: none;
            }
            QPushButton:hover {
                background: #DC2626;
            }
        """)
        close_btn.clicked.connect(self._dismiss)

        h_layout.addWidget(icon_box)
        h_layout.addLayout(title_vbox, 1)
        h_layout.addWidget(brand_lbl)
        h_layout.addWidget(close_btn)

        # ── 2. Content Body ───────────────────────────────────────────────────
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(18, 14, 18, 12)
        body_layout.setSpacing(10)

        # Center highlight banner depending on event
        highlight_box = QWidget()
        highlight_box.setStyleSheet(f"""
            QWidget {{
                background-color: {_BG_SUBTLE};
                border: 1px solid {_BORDER};
                border-radius: 10px;
            }}
        """)
        hl_layout = QVBoxLayout(highlight_box)
        hl_layout.setContentsMargins(14, 10, 14, 10)
        hl_layout.setSpacing(3)

        if event_type == "FARMER_CALLED" or "token" in title.lower():
            tag = QLabel("📢 NOW SERVING AT MANDI COUNTER")
            tag.setStyleSheet(f"color: {_GREEN_MID}; font-weight: 800; font-size: 11px; letter-spacing: 0.5px;")
            main_text = QLabel(title)
            main_text.setStyleSheet(f"color: {_GREEN_DARK}; font-weight: 900; font-size: 26px;")
            main_text.setFont(QFont("Segoe UI", 18, QFont.Bold))
            sub_text = QLabel(message)
            sub_text.setWordWrap(True)
            sub_text.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 13px; font-weight: 500;")

            hl_layout.addWidget(tag)
            hl_layout.addWidget(main_text)
            hl_layout.addWidget(sub_text)

        elif event_type == "PAYMENT_UPDATED":
            tag = QLabel("💰 DIRECT BENEFIT TRANSFER (DBT)")
            tag.setStyleSheet("color: #047857; font-weight: 800; font-size: 11px; letter-spacing: 0.5px;")
            main_text = QLabel(title)
            main_text.setStyleSheet("color: #065F46; font-weight: 900; font-size: 24px;")
            sub_text = QLabel(message)
            sub_text.setWordWrap(True)
            sub_text.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 13px;")

            hl_layout.addWidget(tag)
            hl_layout.addWidget(main_text)
            hl_layout.addWidget(sub_text)

        else:
            tag = QLabel("🌾 PROCUREMENT PLATFORM UPDATE")
            tag.setStyleSheet(f"color: {_GREEN_MID}; font-weight: 800; font-size: 11px;")
            main_text = QLabel(title)
            main_text.setStyleSheet(f"color: {_TEXT_MAIN}; font-weight: 800; font-size: 18px;")
            sub_text = QLabel(message)
            sub_text.setWordWrap(True)
            sub_text.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 13px; line-height: 1.4;")

            hl_layout.addWidget(tag)
            hl_layout.addWidget(main_text)
            hl_layout.addWidget(sub_text)

        body_layout.addWidget(highlight_box, 1)

        # ── 3. Bottom Action Buttons ──────────────────────────────────────────
        action_bar = QHBoxLayout()
        action_bar.setSpacing(10)

        open_btn = QPushButton("🌐 Open KisanSetu Web App →")
        open_btn.setFixedHeight(38)
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_GREEN_MID};
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 700;
                border-radius: 8px;
                padding: 0 16px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {_GREEN_DARK};
            }}
        """)
        open_btn.clicked.connect(self._open_web_app)

        dismiss_btn = QPushButton("Dismiss")
        dismiss_btn.setFixedHeight(38)
        dismiss_btn.setCursor(Qt.PointingHandCursor)
        dismiss_btn.setStyleSheet("""
            QPushButton {{
                background-color: #F1F5F9;
                color: #334155;
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                padding: 0 16px;
                border: 1px solid #CBD5E1;
            }}
            QPushButton:hover {{
                background-color: #E2E8F0;
            }}
        """)
        dismiss_btn.clicked.connect(self._dismiss)

        action_bar.addWidget(open_btn, 1)
        action_bar.addWidget(dismiss_btn)
        body_layout.addLayout(action_bar)

        # ── 4. Bottom Countdown Progress Bar ──────────────────────────────────
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(100)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background: #E2E8F0;
                border: none;
                border-bottom-left-radius: 14px;
                border-bottom-right-radius: 14px;
            }}
            QProgressBar::chunk {{
                background: {_GREEN_LIGHT};
                border-bottom-left-radius: 14px;
            }}
        """)

        card_layout.addWidget(header)
        card_layout.addWidget(body, 1)
        card_layout.addWidget(self._progress)

        outer.addWidget(card)

    # ── Hover Pause Interaction ───────────────────────────────────────────────

    def enterEvent(self, event):
        """Pause auto-dismiss countdown when user hovers over popup."""
        self.is_paused = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Resume countdown when user mouse leaves popup."""
        self.is_paused = False
        super().leaveEvent(event)

    # ── Timer / Auto-dismiss ──────────────────────────────────────────────────

    def _start_timer(self):
        duration_ms = config.popup_duration * 1000
        self._elapsed = 0
        self._interval = 50  # ms per tick

        self._timer = QTimer(self)
        self._timer.setInterval(self._interval)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        self._total_ms = duration_ms

    def _tick(self):
        if self.is_paused:
            return
        self._elapsed += self._interval
        pct = max(0, 100 - int(self._elapsed / self._total_ms * 100))
        self._progress.setValue(pct)
        if self._elapsed >= self._total_ms:
            self._dismiss()

    def _dismiss(self):
        self._timer.stop()
        _PopupStack.remove(self)
        self.close()
        self.deleteLater()

    def _open_web_app(self):
        webbrowser.open(f"{config.frontend_url}")
        self._dismiss()

    def _animate_to_y(self, target_y: int):
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(220)
        anim.setEndValue(QPoint(self.x(), target_y))
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()


# ─── Public API ───────────────────────────────────────────────────────────────

def show_notification(event_type: str, title: str, message: str):
    """
    Create and display a popup. Must be called on the Qt main thread.
    From other threads, use: popup_signals.show.emit(event_type, title, message)
    """
    popup = NotificationPopup(event_type, title, message)
    popup.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    show_notification(
        "FARMER_CALLED",
        "Token A042 Called! (Test)",
        "Please proceed to Mandi Counter 1 immediately. Produce weighing and digital quality inspection ready.",
    )
    # Auto-quit after duration + 2s in test mode
    QTimer.singleShot((config.popup_duration + 2) * 1000, app.quit)
    sys.exit(app.exec_())
