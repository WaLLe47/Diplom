from PySide6.QtWidgets import *
from data.loader import load_csv
from model.build_model import build_model
from solver.solve_model import solve_model


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Cluster Regression MILP"
        )

        layout=QVBoxLayout()

        self.btn=QPushButton(
            "Запустить расчет"
        )

        self.output=QTextEdit()

        self.btn.clicked.connect(
            self.run_model
        )

        layout.addWidget(self.btn)
        layout.addWidget(self.output)

        self.setLayout(layout)


    def run_model(self):

        x,y=load_csv(
           "data/sample_data.csv"
        )

        model=build_model(
           x,y,2,[10,None]
        )

        solve_model(model)

        self.output.append(
            "Решение найдено."
        )