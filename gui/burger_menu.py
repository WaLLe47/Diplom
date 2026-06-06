"""Burger (hamburger) side-drawer with smooth slide animation."""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

DRAWER_WIDTH = 300


class _Separator(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet("background: #30363d; border: none; margin: 4px 2px;")


class _SectionLabel(QLabel):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text.upper(), parent)
        self.setObjectName("sectionTitle")
        self.setContentsMargins(4, 10, 0, 2)


class MenuButton(QPushButton):
    """Full-width action button styled as a menu item."""

    def __init__(
        self,
        icon: str,
        text: str,
        *,
        danger: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(f"  {icon}   {text}", parent)
        self.setObjectName("menuItemDanger" if danger else "menuItem")
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)


class BurgerDrawer(QWidget):
    """Animated side panel that slides in from behind the menu rail."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("sideDrawer")
        self.setFixedWidth(DRAWER_WIDTH)
        self._open = True

        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(240)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        self._build_ui()

    # ─────────────────────────── BUILD ───────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_header())
        root.addWidget(_Separator())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(8, 6, 8, 6)
        body_layout.setSpacing(2)

        # ── Data ──
        body_layout.addWidget(_SectionLabel("Данные"))
        self.load_btn = MenuButton("📂", "Загрузить CSV файл")
        self.preview_btn = MenuButton("👁", "Предпросмотр данных")
        self.preview_btn.setEnabled(False)
        body_layout.addWidget(self.load_btn)
        body_layout.addWidget(self.preview_btn)

        self.file_info = QLabel("Файл не загружен")
        self.file_info.setObjectName("fileInfoLabel")
        self.file_info.setWordWrap(True)
        self.file_info.setContentsMargins(4, 4, 4, 4)
        body_layout.addWidget(self.file_info)

        body_layout.addWidget(_Separator())

        # ── Parameters (filled by MainWindow) ──
        body_layout.addWidget(_SectionLabel("Параметры модели"))
        self.params_container = QWidget()
        params_layout = QVBoxLayout(self.params_container)
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.setSpacing(0)
        body_layout.addWidget(self.params_container)

        body_layout.addWidget(_Separator())

        # ── Actions ──
        body_layout.addWidget(_SectionLabel("Расчёт"))
        self.solve_btn = MenuButton("▶", "Запустить расчёт")
        self.solve_btn.setObjectName("solveBtn")
        self.solve_btn.setMinimumHeight(44)
        body_layout.addWidget(self.solve_btn)

        self.pdf_btn = MenuButton("📄", "Экспортировать отчёт PDF")
        self.pdf_btn.setEnabled(False)
        body_layout.addWidget(self.pdf_btn)

        body_layout.addWidget(_Separator())

        # ── View ──
        body_layout.addWidget(_SectionLabel("Вид"))
        self.theme_btn = MenuButton("🌓", "Переключить тему")
        body_layout.addWidget(self.theme_btn)

        body_layout.addStretch(1)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        # Footer
        root.addWidget(_Separator())
        footer = QLabel("MILP Cluster Analysis  v2.0")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size: 11px; color: #6e7681; padding: 8px 0;")
        root.addWidget(footer)

    def _make_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(52)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 16, 0)
        title = QLabel("MILP Cluster")
        title.setObjectName("drawerTitle")
        layout.addWidget(title)
        layout.addStretch()
        return header

    # ─────────────────────────── ANIMATION ───────────────────────────────────

    def open(self, rail_x: int, window_height: int) -> None:
        """Slide drawer into view starting from behind the rail."""
        self._open = True
        self.show()
        self.raise_()
        start = QRect(rail_x - DRAWER_WIDTH, 0, DRAWER_WIDTH, window_height)
        end   = QRect(rail_x, 0, DRAWER_WIDTH, window_height)
        self._run_anim(start, end)

    def close_drawer(self, rail_x: int, window_height: int) -> None:
        """Slide drawer out of view behind the rail."""
        self._open = False
        start = QRect(rail_x, 0, DRAWER_WIDTH, window_height)
        end   = QRect(rail_x - DRAWER_WIDTH, 0, DRAWER_WIDTH, window_height)
        self._anim.finished.connect(self._on_anim_finished)
        self._run_anim(start, end)

    def _run_anim(self, start: QRect, end: QRect) -> None:
        self._anim.stop()
        try:
            self._anim.finished.disconnect(self._on_anim_finished)
        except RuntimeError:
            pass
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start()

    def _on_anim_finished(self) -> None:
        if not self._open:
            self.hide()
        try:
            self._anim.finished.disconnect(self._on_anim_finished)
        except RuntimeError:
            pass

    def is_open(self) -> bool:
        return self._open
