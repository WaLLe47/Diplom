from PySide6.QtWidgets import *


class SettingsTab(QWidget):

    def __init__(self):

        super().__init__()

        layout=QFormLayout()

        self.r=QSpinBox()
        self.r.setValue(2)

        self.mode=QComboBox()

        self.mode.addItems([
          "Свободные",
          "Частично задать",
          "Равные"
        ])

        self.p1=QLineEdit()

        solve=QPushButton(
           "Решить"
        )

        layout.addRow(
           "Кластеры",
           self.r
        )

        layout.addRow(
           "Режим",
           self.mode
        )

        layout.addRow(
           "|P1|",
           self.p1
        )

        layout.addRow(
           solve
        )

        self.setLayout(
          layout
        )