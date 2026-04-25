from PySide6.QtWidgets import *

class DataTab(QWidget):

    def __init__(self):

        super().__init__()

        layout=QVBoxLayout()

        self.file_button=QPushButton(
            "Загрузить CSV"
        )

        self.file_label=QLabel(
            "Файл не выбран"
        )

        layout.addWidget(
            self.file_button
        )

        layout.addWidget(
            self.file_label
        )

        self.setLayout(
            layout
        )