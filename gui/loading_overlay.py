"""Animated full-screen loading overlay shown while the solver runs."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from gui.styles import THEMES


class _Spinner(QWidget):
    """Rotating arc spinner drawn with QPainter."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(56, 56)
        self._angle = 0
        self._track_color = QColor("#2a3849")
        self._arc_color = QColor("#3dd68c")
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def set_colors(self, track: str, arc: str) -> None:
        self._track_color = QColor(track)
        self._arc_color = QColor(arc)
        self.update()

    def start(self) -> None:
        self._timer.start(16)

    def stop(self) -> None:
        self._timer.stop()

    def _tick(self) -> None:
        self._angle = (self._angle + 5) % 360
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        size = min(self.width(), self.height()) - 10
        x = (self.width() - size) // 2
        y = (self.height() - size) // 2

        track = QPen(self._track_color, 4)
        track.setCapStyle(Qt.RoundCap)
        p.setPen(track)
        p.drawArc(x, y, size, size, 0, 360 * 16)

        arc = QPen(self._arc_color, 4)
        arc.setCapStyle(Qt.RoundCap)
        p.setPen(arc)
        p.drawArc(x, y, size, size, (-self._angle + 90) * 16, 280 * 16)


class LoadingOverlay(QWidget):
    """Semi-transparent overlay with spinner + stage labels + progress bar."""

    _STAGES = [
        ("Построение MILP модели",        "Формируем переменные и ограничения…"),
        ("Решение задачи оптимизации",     "Запускаем HiGHS решатель…"),
        ("Извлечение результатов",         "Обрабатываем кластеры и коэффициенты…"),
        ("Построение графиков",            "Рендерим визуализации Plotly…"),
    ]

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("loadingOverlay")
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self._theme = "dark"

        self._stage = 0
        self._progress = 0
        self._stage_timer = QTimer(self)
        self._stage_timer.timeout.connect(self._next_stage)
        self._progress_timer = QTimer(self)
        self._progress_timer.timeout.connect(self._tick_progress)

        self._dots: list[QLabel] = []
        self._build_ui()
        self.set_theme("dark")
        self.hide()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        card = QWidget()
        card.setObjectName("loadingCard")
        card.setFixedSize(320, 230)
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        self._spinner = _Spinner()
        layout.addWidget(self._spinner, 0, Qt.AlignCenter)

        self._title_lbl = QLabel()
        self._title_lbl.setObjectName("loadingTitle")
        self._title_lbl.setAlignment(Qt.AlignCenter)
        self._title_lbl.setWordWrap(True)

        self._sub_lbl = QLabel()
        self._sub_lbl.setObjectName("loadingSubtitle")
        self._sub_lbl.setAlignment(Qt.AlignCenter)
        self._sub_lbl.setWordWrap(True)

        dots_row = QHBoxLayout()
        dots_row.setSpacing(8)
        dots_row.setAlignment(Qt.AlignCenter)
        for _ in self._STAGES:
            dot = QLabel()
            dot.setObjectName("stageDot")
            dot.setProperty("active", False)
            self._dots.append(dot)
            dots_row.addWidget(dot)

        layout.addWidget(self._title_lbl)
        layout.addWidget(self._sub_lbl)
        layout.addLayout(dots_row)

        self._bar = QProgressBar()
        self._bar.setObjectName("progressBar")
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(5)
        layout.addWidget(self._bar)

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        t = THEMES[theme]
        self._spinner.set_colors(t["border"], t["accent_pink"])

    def show_loading(self) -> None:
        self._stage = 0
        self._progress = 0
        self._bar.setValue(0)
        self._apply_stage(0)
        self.resize(self.parent().size())
        self.show()
        self.raise_()
        self._spinner.start()
        self._stage_timer.start(1800)
        self._progress_timer.start(55)

    def hide_loading(self) -> None:
        self._spinner.stop()
        self._stage_timer.stop()
        self._progress_timer.stop()
        self._bar.setValue(100)
        QTimer.singleShot(350, self.hide)

    def _tick_progress(self) -> None:
        target = min((self._stage + 1) * 25, 90)
        if self._progress < target:
            self._progress += 1
            self._bar.setValue(self._progress)

    def _next_stage(self) -> None:
        self._stage = min(self._stage + 1, len(self._STAGES) - 1)
        self._apply_stage(self._stage)

    def _apply_stage(self, idx: int) -> None:
        title, sub = self._STAGES[idx]
        self._title_lbl.setText(title)
        self._sub_lbl.setText(sub)
        for i, dot in enumerate(self._dots):
            dot.setProperty("active", i <= idx)
            dot.style().unpolish(dot)
            dot.style().polish(dot)

    def resizeEvent(self, event) -> None:  # noqa: N802
        if self.parent():
            self.resize(self.parent().size())
        super().resizeEvent(event)
