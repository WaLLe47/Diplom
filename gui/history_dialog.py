"""History browser for the locally stored datasets, results and PDF reports."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.database import get_db


def _open_pdf_bytes(file_name: str, data: bytes) -> None:
    """Write PDF bytes to a temp file and open it in the system viewer."""
    safe = file_name if file_name.lower().endswith(".pdf") else f"{file_name}.pdf"
    tmp = Path(tempfile.gettempdir()) / safe
    tmp.write_bytes(data)
    if sys.platform == "win32":
        os.startfile(str(tmp))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(tmp)], check=False)
    else:
        subprocess.run(["xdg-open", str(tmp)], check=False)


class HistoryDialog(QWidget):
    """Modal-ish window listing stored datasets / results / reports."""

    dataset_chosen = Signal(int)  # emits dataset id to reload into the app

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("История — локальное хранилище")
        self.setMinimumSize(820, 560)
        self.resize(940, 640)
        self._db = get_db()

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        header = QWidget()
        header.setObjectName("dialogHeader")
        hh = QHBoxLayout(header)
        hh.setContentsMargins(16, 12, 16, 12)
        title = QLabel("🗄  Локальное хранилище")
        title.setObjectName("dialogTitle")
        subtitle = QLabel("Загруженные данные · результаты расчётов · экспортированные PDF")
        subtitle.setObjectName("dialogSubtitle")
        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(title)
        col.addWidget(subtitle)
        hh.addLayout(col, 1)
        root.addWidget(header)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("chartTabs")
        root.addWidget(self._tabs, 1)

        self._ds_table = self._make_table(["ID", "Имя", "Дата", "Строк", "Столбцов"])
        self._res_table = self._make_table(
            ["ID", "Дата", "Набор данных", "Кластеров", "X", "Y", "Ошибка E, %"]
        )
        self._rep_table = self._make_table(["ID", "Дата", "Файл", "Размер, КБ"])

        self._tabs.addTab(self._wrap_datasets(), "Данные")
        self._tabs.addTab(self._wrap_results(), "Результаты")
        self._tabs.addTab(self._wrap_reports(), "PDF-отчёты")

        self.refresh()

    # ── table helpers ─────────────────────────────────────────────────────────

    def _make_table(self, headers: list[str]) -> QTableWidget:
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setSelectionMode(QAbstractItemView.SingleSelection)
        t.verticalHeader().setVisible(False)
        t.setAlternatingRowColors(True)
        t.setShowGrid(False)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        return t

    def _wrap_datasets(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.addWidget(self._ds_table, 1)
        btns = QHBoxLayout()
        btns.addStretch()
        load_btn = QPushButton("↻  Загрузить в программу")
        load_btn.setObjectName("dialogClose")
        load_btn.setCursor(Qt.PointingHandCursor)
        load_btn.clicked.connect(self._load_selected_dataset)
        del_btn = self._delete_button(self._ds_table, "datasets")
        btns.addWidget(del_btn)
        btns.addWidget(load_btn)
        lay.addLayout(btns)
        return w

    def _wrap_results(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.addWidget(self._res_table, 1)
        btns = QHBoxLayout()
        btns.addStretch()
        btns.addWidget(self._delete_button(self._res_table, "results"))
        lay.addLayout(btns)
        return w

    def _wrap_reports(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.addWidget(self._rep_table, 1)
        btns = QHBoxLayout()
        btns.addStretch()
        save_btn = QPushButton("💾  Сохранить как…")
        save_btn.setObjectName("navBtn")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save_selected_report)
        open_btn = QPushButton("📂  Открыть PDF")
        open_btn.setObjectName("dialogClose")
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.clicked.connect(self._open_selected_report)
        btns.addWidget(self._delete_button(self._rep_table, "reports"))
        btns.addWidget(save_btn)
        btns.addWidget(open_btn)
        lay.addLayout(btns)
        return w

    def _delete_button(self, table: QTableWidget, db_table: str) -> QPushButton:
        btn = QPushButton("🗑  Удалить")
        btn.setObjectName("navBtn")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._delete_selected(table, db_table))
        return btn

    @staticmethod
    def _selected_id(table: QTableWidget) -> int | None:
        row = table.currentRow()
        if row < 0:
            return None
        item = table.item(row, 0)
        return int(item.text()) if item else None

    # ── data loading ──────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._fill(self._ds_table, [
            (r["id"], r["name"], r["imported_at"], r["n_rows"], r["n_cols"])
            for r in self._db.list_datasets()
        ])
        self._fill(self._res_table, [
            (
                r["id"], r["created_at"], r["dataset_name"] or "—",
                r["n_clusters"], ", ".join(json.loads(r["x_cols"])), r["y_col"],
                f"{r['error_e']:.4f}",
            )
            for r in self._db.list_results()
        ])
        self._fill(self._rep_table, [
            (r["id"], r["created_at"], r["file_name"], f"{r['size_bytes'] / 1024:.1f}")
            for r in self._db.list_reports()
        ])

    @staticmethod
    def _fill(table: QTableWidget, rows: list[tuple]) -> None:
        table.setRowCount(len(rows))
        for ri, row in enumerate(rows):
            for ci, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if ci == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                table.setItem(ri, ci, item)

    # ── actions ─────────────────────────────────────────────────────────────

    def _load_selected_dataset(self) -> None:
        ds_id = self._selected_id(self._ds_table)
        if ds_id is None:
            QMessageBox.information(self, "История", "Выберите набор данных.")
            return
        self.dataset_chosen.emit(ds_id)

    def _open_selected_report(self) -> None:
        rep_id = self._selected_id(self._rep_table)
        if rep_id is None:
            QMessageBox.information(self, "История", "Выберите отчёт.")
            return
        try:
            name, data = self._db.get_report_pdf(rep_id)
            _open_pdf_bytes(name, data)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть PDF:\n{exc}")

    def _save_selected_report(self) -> None:
        rep_id = self._selected_id(self._rep_table)
        if rep_id is None:
            QMessageBox.information(self, "История", "Выберите отчёт.")
            return
        name, data = self._db.get_report_pdf(rep_id)
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить PDF", name, "PDF (*.pdf)")
        if not path:
            return
        Path(path).write_bytes(data)
        QMessageBox.information(self, "Готово", f"Сохранено:\n{path}")

    def _delete_selected(self, table: QTableWidget, db_table: str) -> None:
        row_id = self._selected_id(table)
        if row_id is None:
            QMessageBox.information(self, "История", "Выберите запись.")
            return
        if QMessageBox.question(
            self, "Удаление", f"Удалить запись #{row_id}?"
        ) != QMessageBox.Yes:
            return
        self._db.delete(db_table, row_id)
        self.refresh()
