from PySide6.QtWidgets import *


class ResultsTab(QWidget):

    def __init__(self):

        super().__init__()

        layout=QVBoxLayout()

        self.table=QTableWidget()

        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels(
            [
             "Кластер",
             "Модель",
             "Ошибка"
            ]
        )

        layout.addWidget(
           self.table
        )

        self.setLayout(layout)