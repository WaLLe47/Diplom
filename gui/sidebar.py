"""Modern persistent sidebar (replaces slide-out drawer)."""

from PySide6.QtCore import Qt, QByteArray, QSize, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
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


_SVG_ICONS: dict[str, str] = {
    "excel": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"'
        ' stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<polyline points="14 2 14 8 20 8"/>'
        '<line x1="8" y1="13" x2="16" y2="13"/>'
        '<line x1="8" y1="17" x2="16" y2="17"/>'
        "</svg>"
    ),
    "eye": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"'
        ' stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>'
        '<circle cx="12" cy="12" r="3"/>'
        "</svg>"
    ),
    "file": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"'
        ' stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<polyline points="14 2 14 8 20 8"/>'
        "</svg>"
    ),
    "close": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"'
        ' stroke="currentColor" stroke-width="2.5" stroke-linecap="round">'
        '<line x1="5" y1="5" x2="19" y2="19"/>'
        '<line x1="19" y1="5" x2="5" y2="19"/>'
        "</svg>"
    ),
}


def _make_icon(name: str, color: str = "#c4b5d8", size: int = 16) -> QIcon:
    svg_src = _SVG_ICONS.get(name, _SVG_ICONS["file"])
    coloured = svg_src.replace('stroke="currentColor"', f'stroke="{color}"')
    data = QByteArray(coloured.encode())
    renderer = QSvgRenderer(data)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    from PySide6.QtGui import QPainter
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)




SIDEBAR_WIDTH = 328
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
        super().__init__(text, parent)
        self.setObjectName("navBtn")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(_make_icon(icon))
        self.setIconSize(QSize(16, 16))


class Sidebar(QWidget):
    """Persistent left sidebar with all controls."""


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
        scroll.setAlignment(Qt.AlignTop)

        body = QWidget()
        body.setObjectName("sidebarBody")
        body.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(14, 2, 14, 8)
        self._body_layout.setSpacing(2)

        self._build_data_section()
        self._body_layout.addWidget(_HSep())
        self._build_params_section()
        self._body_layout.addWidget(_HSep())
        self._build_actions_section()
        self._body_layout.addStretch(1)

        scroll.setWidget(body)
        root.addWidget(scroll, 1)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("sidebarHeader")
        header.setFixedHeight(52)
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(14, 4, 14, 4)
        hlay.setSpacing(10)

        self.close_btn = QPushButton()
        self.close_btn.setObjectName("burgerBtn")
        self.close_btn.setToolTip("Закрыть меню")
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setIcon(_make_icon("close", color="#d4c8e8", size=18))
        self.close_btn.setIconSize(QSize(16, 16))
        self.close_btn.setCursor(Qt.PointingHandCursor)
        hlay.addWidget(self.close_btn, 0, Qt.AlignVCenter)

        logo = QLabel("M")
        logo.setObjectName("logoBadge")
        hlay.addWidget(logo, 0, Qt.AlignVCenter)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title_col.setContentsMargins(0, 0, 0, 0)

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

        self.load_btn = NavButton("excel", "Загрузить Excel")
        self._body_layout.addWidget(self.load_btn)

        self.preview_btn = NavButton("eye",   "Предпросмотр")
        self.preview_btn.setEnabled(False)
        self._body_layout.addWidget(self.preview_btn)

        self.file_badge = QLabel("Файл не загружен")
        self.file_badge.setObjectName("fileInfoBadge")
        self.file_badge.setWordWrap(True)
        self._body_layout.addWidget(self.file_badge)

        self.history_btn = NavButton("file", "История (хранилище)")
        self._body_layout.addWidget(self.history_btn)

    def _build_params_section(self) -> None:
        self._body_layout.addWidget(_Section("Параметры"))

        card = QWidget()
        card.setObjectName("paramsCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(10, 8, 10, 8)
        card_lay.setSpacing(0)

        form = QFormLayout()
        form.setVerticalSpacing(6)
        form.setHorizontalSpacing(10)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)

        self.r_spin = QSpinBox()
        self.r_spin.setRange(2, 50)
        self.r_spin.setValue(2)
        r_label = QLabel("Кластеры (r)")
        r_label.setObjectName("formLabel")
        form.addRow(r_label, self.r_spin)

        mode_widget = QWidget()
        mode_widget.setObjectName("modeToggle")
        mode_row = QHBoxLayout(mode_widget)
        mode_row.setContentsMargins(0, 0, 0, 0)
        mode_row.setSpacing(0)

        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self._mode_btns = []
        _mode_names = ("modeBtnLeft", "modeBtnMid", "modeBtnRight")
        for idx, (text, obj_name) in enumerate(
            zip(["Свободный", "Ручной", "Поровну"], _mode_names)
        ):
            btn = QPushButton(text)
            btn.setObjectName(obj_name)
            btn.setCheckable(True)
            btn.setChecked(idx == 0)
            btn.setFixedHeight(32)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setCursor(Qt.PointingHandCursor)
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
        self._partial_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._partial_form = QFormLayout(self._partial_widget)
        self._partial_form.setContentsMargins(0, 4, 0, 0)
        self._partial_form.setVerticalSpacing(6)
        self._partial_form.setHorizontalSpacing(10)
        self._partial_widget.setVisible(False)
        self.partial_inputs: list[QLineEdit] = []
        card_lay.addWidget(self._partial_widget)

        self.r_spin.valueChanged.connect(self._rebuild_partial)
        self._rebuild_partial()

    def _build_actions_section(self) -> None:
        self._body_layout.addWidget(_Section("Расчёт"))

        self.solve_btn = QPushButton("▶   Запустить расчёт")
        self.solve_btn.setObjectName("navBtnPrimary")
        self.solve_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.solve_btn.setCursor(Qt.PointingHandCursor)
        self._body_layout.addWidget(self.solve_btn)

        self.pdf_btn = NavButton("file",  "Экспорт PDF")
        self.pdf_btn.setEnabled(False)
        self._body_layout.addWidget(self.pdf_btn)

    # ─────────────────────────── SLOTS ───────────────────────────────────────


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
        self.file_badge.setText(f"{name}\n{n} наблюдений")
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