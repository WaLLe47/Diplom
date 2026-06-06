"""Reusable dialog windows."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class DataPreviewDialog(QDialog):
    """Modal dialog showing loaded CSV data in a table."""

    def __init__(
        self,
        file_path: str,
        x: list[float],
        y: list[float],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Предпросмотр данных")
        self.setMinimumSize(560, 520)
        self.resize(620, 580)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        header = QWidget()
        header.setObjectName("dialogHeader")
        header_lay = QHBoxLayout(header)
        header_lay.setContentsMargins(18, 16, 18, 16)
        header_lay.setSpacing(16)

        icon = QLabel("📊")
        icon.setStyleSheet("font-size: 30px; background: transparent;")

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        file_label = QLabel(Path(file_path).name)
        file_label.setObjectName("dialogTitle")
        rows_label = QLabel(f"Загружено наблюдений: {len(x)}")
        rows_label.setObjectName("dialogSubtitle")
        text_col.addWidget(file_label)
        text_col.addWidget(rows_label)

        header_lay.addWidget(icon)
        header_lay.addLayout(text_col, 1)
        layout.addWidget(header)

        table_card = QWidget()
        table_card.setObjectName("dialogTableCard")
        table_lay = QVBoxLayout(table_card)
        table_lay.setContentsMargins(12, 12, 12, 12)

        table = QTableWidget(len(x), 3)
        table.setHorizontalHeaderLabels(["№", "x", "y"])
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setStyleSheet("border: none; border-radius: 8px;")

        for row_idx, (xv, yv) in enumerate(zip(x, y), start=1):
            num = QTableWidgetItem(str(row_idx))
            num.setTextAlignment(Qt.AlignCenter)
            table.setItem(row_idx - 1, 0, num)
            table.setItem(row_idx - 1, 1, QTableWidgetItem(f"{xv:.4f}"))
            table.setItem(row_idx - 1, 2, QTableWidgetItem(f"{yv:.4f}"))

        table_lay.addWidget(table)
        layout.addWidget(table_card, 1)

        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("dialogClose")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
