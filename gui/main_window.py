from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

from data.loader import load_csv
from model.build_model import build_model
from solver.solve_model import solve_model
from analysis.extract_results import extract_results
from visualization.plot_clusters import plot_clusters


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.csv_path = None

        self.setWindowTitle(
            "Cluster Regression MILP"
        )

        self.resize(700,500)

        layout = QVBoxLayout()


        # ------------------
        # выбор файла
        # ------------------

        file_layout = QHBoxLayout()

        self.file_label = QLabel(
            "CSV не выбран"
        )

        self.load_btn = QPushButton(
            "Загрузить CSV"
        )

        self.load_btn.clicked.connect(
            self.load_file
        )

        file_layout.addWidget(
            self.load_btn
        )
        file_layout.addWidget(
            self.file_label
        )


        # ------------------
        # число кластеров
        # ------------------

        r_layout = QHBoxLayout()

        r_layout.addWidget(
            QLabel("Кластеров r:")
        )

        self.r_input=QSpinBox()
        self.r_input.setMinimum(2)
        self.r_input.setValue(2)

        r_layout.addWidget(
            self.r_input
        )


        # ------------------
        # размер первого кластера
        # ------------------

        size_layout=QHBoxLayout()

        size_layout.addWidget(
            QLabel("|P1| (0 = свободно)")
        )

        self.cluster_size=QSpinBox()
        self.cluster_size.setMinimum(0)
        self.cluster_size.setValue(0)

        size_layout.addWidget(
            self.cluster_size
        )


        # ------------------
        # запуск
        # ------------------

        self.solve_btn = QPushButton(
            "Запустить расчет"
        )

        self.solve_btn.clicked.connect(
            self.run_model
        )


        # ------------------
        # вывод
        # ------------------

        self.output=QTextEdit()
        self.output.setReadOnly(True)


        # ------------------
        # layout
        # ------------------

        layout.addLayout(file_layout)
        layout.addLayout(r_layout)
        layout.addLayout(size_layout)

        layout.addWidget(
            self.solve_btn
        )

        layout.addWidget(
            self.output
        )

        self.setLayout(layout)


    def load_file(self):

        file_name,_=QFileDialog.getOpenFileName(
            self,
            "Выбери CSV",
            "",
            "CSV Files (*.csv)"
        )

        if file_name:
            self.csv_path=file_name
            self.file_label.setText(
                file_name
            )


    def run_model(self):

        if not self.csv_path:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Сначала выбери CSV"
            )
            return


        try:

            self.output.clear()

            x,y = load_csv(
                self.csv_path
            )

            r=self.r_input.value()

            p1=self.cluster_size.value()

            if p1==0:
                cluster_sizes=None
            else:
                cluster_sizes=[p1,None]


            self.output.append(
                "Строим модель..."
            )

            model=build_model(
                x,
                y,
                r,
                cluster_sizes
            )

            self.output.append(
                "Решаем..."
            )

            solve_model(model)

            results=extract_results(
                model,
                x,
                y,
                r
            )

            self.output.append(
                "\nКластеры:"
            )

            for j,pts in results["clusters"].items():

                self.output.append(
                    f"P{j+1}: {[k+1 for k in pts]}"
                )


            self.output.append(
                "\nРегрессии:"
            )

            for j,(a0,a1) in enumerate(
                results["coeffs"]
            ):
                self.output.append(
                    f"{j+1}: "
                    f"y={a0:.2f}+{a1:.2f}x"
                )

            self.output.append(
                "\nГрафик откроется отдельно..."
            )

            plot_clusters(
                results,
                x,
                y
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Ошибка",
                str(e)
            )