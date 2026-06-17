"""Reusable dialog windows."""

from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class DataPreviewDialog(QDialog):
    """Modal dialog: shows CSV data and lets the user pick X / Y columns."""

    def __init__(
        self,
        file_path: str,
        df: pd.DataFrame,
        x_cols: list[str] | None = None,
        y_col: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Предпросмотр данных Excel")
        self.setMinimumSize(760, 600)
        self.resize(860, 660)

        self._df = df
        self._cols = list(df.columns)

        # Defaults: last col = Y, rest = X
        self._x_checks: dict[str, QCheckBox] = {}
        self._y_radios: dict[str, QRadioButton] = {}
        # Non-exclusive group: we enforce "exactly one Y" manually so the Y radio
        # can be cleared programmatically (an exclusive group refuses to uncheck
        # its only active button, which let a column be both X and Y at once).
        self._y_group = QButtonGroup(self)
        self._y_group.setExclusive(False)
        self._syncing = False  # re-entrancy guard for the cross-uncheck signals

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── File header ───────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("dialogHeader")
        hh = QHBoxLayout(header)
        hh.setContentsMargins(16, 14, 16, 14)
        hh.setSpacing(14)

        icon = QLabel("📊")
        icon.setStyleSheet("font-size: 26px; background: transparent;")
        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        lbl_name = QLabel(Path(file_path).name)
        lbl_name.setObjectName("dialogTitle")
        lbl_rows = QLabel(f"Строк: {len(df)}  ·  Числовых столбцов: {len(df.columns)}")
        lbl_rows.setObjectName("dialogSubtitle")
        text_col.addWidget(lbl_name)
        text_col.addWidget(lbl_rows)
        hh.addWidget(icon)
        hh.addLayout(text_col, 1)
        layout.addWidget(header)

        # ── Column selector + table (side by side) ────────────────────────────
        body_row = QHBoxLayout()
        body_row.setSpacing(14)

        # Left: column role selector
        col_card = QWidget()
        col_card.setObjectName("dialogHeader")
        col_card.setFixedWidth(230)
        col_layout = QVBoxLayout(col_card)
        col_layout.setContentsMargins(14, 14, 14, 14)
        col_layout.setSpacing(10)

        role_title = QLabel("Роли столбцов")
        role_title.setObjectName("dialogTitle")
        role_title.setStyleSheet("font-size: 13px; font-weight: 700;")
        col_layout.addWidget(role_title)

        hint = QLabel("☑ Независимые переменные (X)\n◉ Зависимая переменная (Y)")
        hint.setObjectName("dialogSubtitle")
        hint.setWordWrap(True)
        col_layout.addWidget(hint)

        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255,255,255,0.10);")
        col_layout.addWidget(sep)

        # Header row
        hdr_row = QHBoxLayout()
        hdr_row.setContentsMargins(0, 0, 0, 0)
        hdr_x = QLabel("X")
        hdr_x.setFixedWidth(28)
        hdr_x.setAlignment(Qt.AlignCenter)
        hdr_x.setToolTip("Независимая переменная (предиктор)")
        hdr_x.setStyleSheet("font-weight:700; color:#26c6da; font-size:12px;")
        hdr_y = QLabel("Y")
        hdr_y.setFixedWidth(28)
        hdr_y.setAlignment(Qt.AlignCenter)
        hdr_y.setToolTip("Зависимая переменная (цель)")
        hdr_y.setStyleSheet("font-weight:700; color:#e040fb; font-size:12px;")
        hdr_col = QLabel("Столбец")
        hdr_col.setStyleSheet("font-weight:700; color:rgba(255,255,255,0.50); font-size:12px;")
        hdr_row.addWidget(hdr_x)
        hdr_row.addWidget(hdr_y)
        hdr_row.addWidget(hdr_col, 1)
        col_layout.addLayout(hdr_row)

        scroll_cols = QScrollArea()
        scroll_cols.setWidgetResizable(True)
        scroll_cols.setFrameShape(QFrame.NoFrame)
        scroll_cols.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(0, 0, 0, 0)
        inner_lay.setSpacing(4)

        default_y = y_col if y_col in self._cols else self._cols[-1]
        default_xs = set(x_cols) if x_cols else set(self._cols) - {default_y}

        for col in self._cols:
            row = QHBoxLayout()
            row.setContentsMargins(0, 2, 0, 2)
            row.setSpacing(0)

            cb = QCheckBox()
            cb.setFixedWidth(28)
            cb.setChecked(col in default_xs)
            cb.setStyleSheet(
                "QCheckBox::indicator { width:16px; height:16px; }"
                "QCheckBox::indicator:checked { background:#26c6da; border:2px solid #26c6da; border-radius:3px; }"
                "QCheckBox { color: rgba(255,255,255,0.80); }"
            )
            self._x_checks[col] = cb

            rb = QRadioButton()
            rb.setFixedWidth(28)
            rb.setChecked(col == default_y)
            rb.setStyleSheet(
                "QRadioButton::indicator { width:16px; height:16px; }"
                "QRadioButton::indicator:checked { background:#e040fb; border:2px solid #e040fb; }"
            )
            self._y_group.addButton(rb)
            self._y_radios[col] = rb

            # Y selected → uncheck X, X checked → uncheck Y
            rb.toggled.connect(lambda checked, c=col: self._on_y_toggled(c, checked))
            cb.stateChanged.connect(lambda state, c=col: self._on_x_changed(c, state))

            lbl = QLabel(col)
            lbl.setToolTip(col)
            lbl.setStyleSheet("font-size: 12px;")

            row.addWidget(cb)
            row.addWidget(rb)
            row.addWidget(lbl, 1)
            inner_lay.addLayout(row)

        inner_lay.addStretch()
        scroll_cols.setWidget(inner)
        col_layout.addWidget(scroll_cols, 1)

        legend_sep = QWidget()
        legend_sep.setFixedHeight(1)
        legend_sep.setStyleSheet("background: rgba(255,255,255,0.10);")
        col_layout.addWidget(legend_sep)
        legend = QLabel("X — независимые \nY — зависимая ")
        legend.setObjectName("dialogSubtitle")
        legend.setWordWrap(True)
        legend.setStyleSheet("font-size:12px; color:rgba(255,255,255,0.45); padding:4px 0;")
        col_layout.addWidget(legend)

        body_row.addWidget(col_card)

        # Right: data table
        table_card = QWidget()
        table_card.setObjectName("dialogTableCard")
        table_lay = QVBoxLayout(table_card)
        table_lay.setContentsMargins(10, 10, 10, 10)

        n_cols = len(self._cols)
        self._table = QTableWidget(len(df), n_cols + 1)
        self._table.setHorizontalHeaderLabels(["№"] + self._cols)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for ci in range(1, n_cols + 1):
            self._table.horizontalHeader().setSectionResizeMode(ci, QHeaderView.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.setStyleSheet("border: none;")

        for ri, row_data in enumerate(df.itertuples(index=False)):
            num = QTableWidgetItem(str(ri + 1))
            num.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(ri, 0, num)
            for ci, val in enumerate(row_data):
                self._table.setItem(ri, ci + 1, QTableWidgetItem(f"{val:.4f}"))

        table_lay.addWidget(self._table)
        body_row.addWidget(table_card, 1)
        layout.addLayout(body_row, 1)

        # ── Footer buttons ────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("dialogClose")
        cancel_btn.setMinimumWidth(110)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(
            "background: rgba(255,255,255,0.07); color: rgba(255,255,255,0.70);"
            "border: 1px solid rgba(255,255,255,0.12); border-radius: 8px;"
            "padding: 10px 24px; font-size: 13px; font-weight: 600;"
        )

        apply_btn = QPushButton("✓  Применить выбор")
        apply_btn.setObjectName("dialogClose")
        apply_btn.setMinimumWidth(130)
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.clicked.connect(self._on_apply)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(apply_btn)
        layout.addLayout(btn_row)

        # Result fields (populated on accept)
        self.selected_x_cols: list[str] = []
        self.selected_y_col: str = ""

    # ── slots ──────────────────────────────────────────────────────────────────

    def _on_y_toggled(self, col: str, checked: bool) -> None:
        if self._syncing:
            return
        if not checked:
            # Keep exactly one Y: re-assert it if the user clicked the active one
            # and no other target is selected.
            if not any(rb.isChecked() for rb in self._y_radios.values()):
                self._syncing = True
                self._y_radios[col].setChecked(True)
                self._syncing = False
            return
        self._syncing = True
        try:
            # Manual exclusivity: this column becomes the only Y…
            for other, rb in self._y_radios.items():
                if other != col and rb.isChecked():
                    rb.setChecked(False)
            # …and a column cannot be both predictor (X) and target (Y).
            self._x_checks[col].setChecked(False)
        finally:
            self._syncing = False

    def _on_x_changed(self, col: str, state: int) -> None:
        if self._syncing or state != Qt.Checked.value:
            return
        self._syncing = True
        try:
            self._y_radios[col].setChecked(False)
        finally:
            self._syncing = False

    def _on_apply(self) -> None:
        y_col = next(
            (c for c, rb in self._y_radios.items() if rb.isChecked()), None
        )
        if y_col is None:
            QMessageBox.warning(self, "Выбор столбцов", "Выберите столбец Y (целевую переменную).")
            return

        x_cols = [c for c, cb in self._x_checks.items() if cb.isChecked()]
        if not x_cols:
            QMessageBox.warning(self, "Выбор столбцов", "Выберите хотя бы один столбец X.")
            return

        self.selected_x_cols = x_cols
        self.selected_y_col = y_col
        self.accept()