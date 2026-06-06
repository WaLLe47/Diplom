"""Animated toggle switch widget (like iOS/Material switch)."""

from PySide6.QtCore import (
    Property, QEasingCurve, QPropertyAnimation, QRectF, Qt, Signal
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QAbstractButton, QSizePolicy


class ToggleSwitch(QAbstractButton):
    """Smooth animated on/off toggle switch."""

    toggled_state: Signal = Signal(bool)

    _W, _H = 46, 26

    def __init__(self, parent=None, *, checked: bool = False) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)

        self._track_on = QColor("#3dd68c")
        self._track_off = QColor("#2a3849")
        self._knob = QColor("#ffffff")

        self._knob_x: float = self._knob_on_x() if checked else self._knob_off_x()
        self._anim = QPropertyAnimation(self, b"knob_x", self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.clicked.connect(self._on_click)

    def set_colors(self, track_on: str, track_off: str) -> None:
        self._track_on = QColor(track_on)
        self._track_off = QColor(track_off)
        self.update()

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(self._W, self._H)

    def _knob_off_x(self) -> float:
        return 3.0

    def _knob_on_x(self) -> float:
        return float(self._W - self._H + 3)

    def _get_knob_x(self) -> float:
        return self._knob_x

    def _set_knob_x(self, val: float) -> None:
        self._knob_x = val
        self.update()

    knob_x = Property(float, _get_knob_x, _set_knob_x)

    def _on_click(self) -> None:
        target = self._knob_on_x() if self.isChecked() else self._knob_off_x()
        self._anim.stop()
        self._anim.setStartValue(self._knob_x)
        self._anim.setEndValue(target)
        self._anim.start()
        self.toggled_state.emit(self.isChecked())

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)

        track_color = self._track_on if self.isChecked() else self._track_off
        p.setBrush(track_color)
        radius = self._H / 2
        p.drawRoundedRect(QRectF(0, 0, self._W, self._H), radius, radius)

        p.setBrush(self._knob)
        knob_d = self._H - 6
        p.drawEllipse(QRectF(self._knob_x, 3, knob_d, knob_d))
