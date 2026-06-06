"""Modern persistent sidebar (replaces slide-out drawer)."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from gui.toggle_switch import ToggleSwitch

SIDEBAR_WIDTH = 288
DRAWER_MARGIN = 12
TOP_BAR_HEIGHT = 60


class _HSep(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("hSep")
        self.setFixedHeight(1)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


class _Section(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("navSection")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


class NavButton(QPushButton):
    def __init__(self, icon: str, text: str, *, danger=False, parent=None):
        super().__init__(f"  {icon}   {text}", parent)
        self.setObjectName("navBtn")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(38)
        self.setCursor(Qt.PointingHandCursor)


class Sidebar(QWidget):
    """Persistent left sidebar with all controls."""

    theme_changed = Signal(bool)   # True = dark

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._build()

    # ─────────────────────────── BUILD ───────────────────────────────────────

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        body = QWidget()
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(10, 8, 10, 8)
        self._body_layout.setSpacing(2)

        self._build_data_section()
        self._body_layout.addWidget(_HSep())
        self._build_params_section()
        self._body_layout.addWidget(_HSep())
        self._build_actions_section()
        self._body_layout.addStretch(1)

        scroll.setWidget(body)
        root.addWidget(scroll, 1)
        root.addWidget(self._build_footer())

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("sidebarHeader")
        header.setFixedHeight(64)
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(12, 10, 12, 10)
        hlay.setSpacing(10)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("burgerBtn")
        self.close_btn.setToolTip("Закрыть меню")
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        hlay.addWidget(self.close_btn, 0, Qt.AlignTop)

        logo = QLabel("◈")
        logo.setObjectName("logoBadge")
        hlay.addWidget(logo, 0, Qt.AlignTop)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title_col.setContentsMargins(0, 2, 0, 0)

        title = QLabel("MILP Cluster")
        title.setObjectName("appTitle")
        subtitle = QLabel("Кластерная регрессия")
        subtitle.setObjectName("appSubtitle")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        hlay.addLayout(title_col, 1)

        return header

    def _build_data_section(self) -> None:
        self._body_layout.addWidget(_Section("Данные"))

        self.load_btn = NavButton("📂", "Загрузить CSV")
        self._body_layout.addWidget(self.load_btn)

        self.preview_btn = NavButton("👁", "Предпросмотр")
        self.preview_btn.setEnabled(False)
        self._body_layout.addWidget(self.preview_btn)

        self.file_badge = QLabel("Файл не загружен")
        self.file_badge.setObjectName("fileInfoBadge")
        self.file_badge.setWordWrap(True)
        self._body_layout.addWidget(self.file_badge)

    def _build_params_section(self) -> None:
        self._body_layout.addWidget(_Section("Параметры"))

        card = QWidget()
        card.setObjectName("paramsCard")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(12, 10, 12, 10)
        card_lay.setSpacing(10)

        form = QFormLayout()
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(12)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.r_spin = QSpinBox()
        self.r_spin.setRange(2, 50)
        self.r_spin.setValue(2)
        r_label = QLabel("Кластеры (r)")
        r_label.setObjectName("formLabel")
        form.addRow(r_label, self.r_spin)

        mode_widget = QWidget()
        mode_row = QHBoxLayout(mode_widget)
        mode_row.setContentsMargins(0, 0, 0, 0)
        mode_row.setSpacing(4)

        self.mode_group = QButtonGroup(self)
        self._mode_btns = []
        for idx, text in enumerate(["Своб.", "Ручной", "Поровну"]):
            btn = QPushButton(text)
            btn.setObjectName("modeBtn")
            btn.setCheckable(True)
            btn.setChecked(idx == 0)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(30)
            self.mode_group.addButton(btn, idx)
            mode_row.addWidget(btn)
            self._mode_btns.append(btn)

        self.mode_group.idClicked.connect(self._on_mode_change)
        size_label = QLabel("Размеры")
        size_label.setObjectName("formLabel")
        form.addRow(size_label, mode_widget)

        card_lay.addLayout(form)
        self._body_layout.addWidget(card)

        self._partial_widget = QWidget()
        self._partial_form = QFormLayout(self._partial_widget)
        self._partial_form.setContentsMargins(12, 0, 12, 4)
        self._partial_form.setVerticalSpacing(8)
        self._partial_form.setHorizontalSpacing(12)
        self._partial_widget.setVisible(False)
        self.partial_inputs: list[QLineEdit] = []
        self._body_layout.addWidget(self._partial_widget)

        self.r_spin.valueChanged.connect(self._rebuild_partial)
        self._rebuild_partial()

    def _build_actions_section(self) -> None:
        self._body_layout.addWidget(_Section("Расчёт"))

        self.solve_btn = QPushButton("▶   Запустить расчёт")
        self.solve_btn.setObjectName("navBtnPrimary")
        self.solve_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.solve_btn.setCursor(Qt.PointingHandCursor)
        self._body_layout.addWidget(self.solve_btn)

        self.pdf_btn = NavButton("📄", "Экспорт PDF")
        self.pdf_btn.setEnabled(False)
        self._body_layout.addWidget(self.pdf_btn)

    def _build_footer(self) -> QWidget:
        footer = QWidget()
        footer.setObjectName("sidebarFooter")
        footer.setFixedHeight(56)
        lay = QHBoxLayout(footer)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(10)

        theme_lbl = QLabel("Тёмная")
        theme_lbl.setObjectName("themeLabel")
        lay.addWidget(theme_lbl)
        lay.addStretch()

        self.theme_toggle = ToggleSwitch(checked=True)
        self.theme_toggle.toggled_state.connect(self._on_theme_toggle)
        lay.addWidget(self.theme_toggle)

        ver = QLabel("v2.0")
        ver.setObjectName("versionLabel")
        lay.addWidget(ver)

        self._theme_label = theme_lbl
        return footer

    # ─────────────────────────── SLOTS ───────────────────────────────────────

    def _on_theme_toggle(self, checked: bool) -> None:
        self._theme_label.setText("Тёмная" if checked else "Светлая")
        self.theme_changed.emit(checked)

    def _on_mode_change(self, mode_id: int) -> None:
        self._partial_widget.setVisible(mode_id == 1)

    def _rebuild_partial(self) -> None:
        while self._partial_form.count():
            child = self._partial_form.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.partial_inputs = []
        r = self.r_spin.value()
        for idx in range(r - 1):
            edit = QLineEdit()
            edit.setPlaceholderText("авто")
            lbl = QLabel(f"|P{idx + 1}|")
            lbl.setObjectName("formLabel")
            self._partial_form.addRow(lbl, edit)
            self.partial_inputs.append(edit)
        self._partial_widget.setVisible(self.mode_group.checkedId() == 1)

    # ─────────────────────────── PUBLIC HELPERS ──────────────────────────────

    def set_file_loaded(self, name: str, n: int) -> None:
        self.file_badge.setText(f"📊  {name}\n{n} наблюдений")
        self.preview_btn.setEnabled(True)

    def set_solving(self, active: bool) -> None:
        self.solve_btn.setEnabled(not active)
        self.solve_btn.setText(
            "  ⏳  Идёт расчёт…" if active else "▶   Запустить расчёт"
        )
        if active:
            self.pdf_btn.setEnabled(False)

    def get_cluster_sizes(self, n: int, r: int) -> list[int | None] | None:
        mode = self.mode_group.checkedId()
        if mode == 0:
            return None
        if mode == 2:
            base = n // r
            sizes = [base] * r
            sizes[-1] = n - base * (r - 1)
            return sizes
        sizes: list[int | None] = [None] * r
        fixed = 0
        for idx, edit in enumerate(self.partial_inputs):
            raw = edit.text().strip()
            if not raw:
                continue
            s = int(raw)
            if s < 0:
                raise ValueError("Размер кластера не может быть отрицательным")
            sizes[idx] = s
            fixed += s
        sizes[-1] = n - fixed
        if sizes[-1] <= 0:
            raise ValueError("Некорректное разбиение: последний кластер ≤ 0")
        return sizes
