"""
KisanSetu Notifier — Custom Popup Window.

Renders a frameless, always-on-top QWidget at the bottom-right corner
of the screen — completely independent of Windows Action Center / toasts.

Features:
  - Frameless green KisanSetu header with event icon + title
  - Message body
  - Auto-dismiss countdown progress bar (configurable duration)
  - Click anywhere to dismiss early
  - Stacking: multiple popups slide upward without overlapping
  - Thread-safe: call show_notification() from any thread via Qt signal
"""
import sys
from typing import ClassVar

from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QPoint, pyqtSignal, QObject
)
from PyQt5.QtGui import QColor, QFont, QPainter, QPainterPath
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QDesktopWidget
)

from config import config

# ─── KisanSetu brand colours ─────────────────────────────────────────────────
_GREEN  = "#2E7D32"
_GREEN2 = "#388E3C"
_WHITE  = "#FFFFFF"
_BG     = "#FAFAFA"
_TEXT   = "#212121"
_BORDER = "#C8E6C9"

# ─── Event metadata ──────────────────────────────────────────────────────────
_EVENT_META: dict[str, tuple[str, str]] = {
    "FARMER_CALLED":      ("🔔", "Token Called!"),
    "BOOKING_CONFIRMED":  ("✅", "Booking Confirmed"),
    "PAYMENT_UPDATED":    ("💰", "Payment Update"),
    "QUEUE_UPDATED":      ("📋", "Queue Update"),
    "NOTIFICATION":       ("🌾", "KisanSetu"),
}
_POPUP_W = 320
_POPUP_H = 110
_MARGIN  = 16    # gap from screen edge and between stacked popups


class _PopupSignals(QObject):
    """Bridge: allows any thread to safely trigger a popup on the Qt main thread."""
    show = pyqtSignal(str, str, str)   # event_type, title, message


# Singleton signal object — import and call .show.emit() from anywhere
popup_signals = _PopupSignals()


class _PopupStack:
    """Tracks currently visible popups so they stack upward."""
    _active: ClassVar[list["NotificationPopup"]] = []

    @classmethod
    def add(cls, popup: "NotificationPopup") -> int:
        """Register popup and return its Y position (from bottom of screen)."""
        cls._active.append(popup)
        return len(cls._active)

    @classmethod
    def remove(cls, popup: "NotificationPopup"):
        if popup in cls._active:
            cls._active.remove(popup)
        # Slide remaining popups down
        for i, p in enumerate(cls._active):
            target_y = _bottom_right_y(i + 1)
            p._animate_to_y(target_y)

    @classmethod
    def count(cls) -> int:
        return len(cls._active)


def _bottom_right_pos(stack_index: int) -> QPoint:
    """Compute screen position for popup at stack_index (1-based, bottom-right)."""
    screen = QDesktopWidget().availableGeometry()
    x = screen.right() - _POPUP_W - _MARGIN
    y = screen.bottom() - (_POPUP_H + _MARGIN) * stack_index
    return QPoint(x, y)


def _bottom_right_y(stack_index: int) -> int:
    screen = QDesktopWidget().availableGeometry()
    return screen.bottom() - (_POPUP_H + _MARGIN) * stack_index


class NotificationPopup(QWidget):
    """
    A single custom popup notification window.
    Uses Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint —
    completely bypasses Windows Action Center.
    """

    def __init__(self, event_type: str, title: str, message: str):
        super().__init__()

        icon, default_title = _EVENT_META.get(event_type, ("🌾", "KisanSetu"))
        display_title = title or default_title

        self.setWindowFlags(
            Qt.Tool |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(_POPUP_W, _POPUP_H)

        # Position at bottom-right, stacked
        stack_idx = _PopupStack.add(self)
        pos = _bottom_right_pos(stack_idx)
        self.move(pos)

        self._build_ui(icon, display_title, message)
        self._start_timer()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self, icon: str, title: str, message: str):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Container widget (rounded corners, shadow via stylesheet)
        card = QWidget(self)
        card.setObjectName("card")
        card.setStyleSheet(f"""
            QWidget#card {{
                background: {_BG};
                border: 1px solid {_BORDER};
                border-radius: 8px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 8)
        card_layout.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(32)
        header.setStyleSheet(f"""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {_GREEN}, stop:1 {_GREEN2}
            );
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(10, 0, 10, 0)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"color: {_WHITE}; font-size: 15px; background: transparent;")

        title_lbl = QLabel(title[:38])
        title_lbl.setStyleSheet(f"color: {_WHITE}; font-weight: bold; font-size: 11px; background: transparent;")
        title_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))

        app_lbl = QLabel("KisanSetu")
        app_lbl.setStyleSheet(f"color: rgba(255,255,255,0.7); font-size: 9px; background: transparent;")

        h_layout.addWidget(icon_lbl)
        h_layout.addSpacing(6)
        h_layout.addWidget(title_lbl, 1)
        h_layout.addWidget(app_lbl)

        # ── Message body ──────────────────────────────────────────────────────
        msg_lbl = QLabel(message[:120])
        msg_lbl.setWordWrap(True)
        msg_lbl.setContentsMargins(12, 6, 12, 4)
        msg_lbl.setStyleSheet(f"color: {_TEXT}; font-size: 10px; background: transparent;")
        msg_lbl.setFont(QFont("Segoe UI", 9))

        # ── Progress bar (countdown) ──────────────────────────────────────────
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(100)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(3)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background: {_BORDER};
                border: none;
                border-radius: 0px;
            }}
            QProgressBar::chunk {{
                background: {_GREEN};
                border-radius: 0px;
            }}
        """)

        card_layout.addWidget(header)
        card_layout.addWidget(msg_lbl, 1)
        card_layout.addWidget(self._progress)

        outer.addWidget(card)

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

    def _animate_to_y(self, target_y: int):
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(200)
        anim.setEndValue(QPoint(self.x(), target_y))
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()

    # ── Click to dismiss ──────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        self._dismiss()


# ─── Public API ───────────────────────────────────────────────────────────────

def show_notification(event_type: str, title: str, message: str):
    """
    Create and display a popup. Must be called on the Qt main thread.
    From other threads, use: popup_signals.show.emit(event_type, title, message)
    """
    popup = NotificationPopup(event_type, title, message)
    popup.show()
