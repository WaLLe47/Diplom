from PySide6.QtWidgets import (
    QFileDialog,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from analysis.extract_results import extract_results
from analysis.metrics import mean_percent_error
from data.loader import load_csv
from model.build_model import build_model
from solver.solve_model import solve_model
from visualization.plot_clusters import plot_clusters


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.csv_path = None

        self.setWindowTitle("Cluster Regression MILP")
        self.resize(1000, 700)

        root_layout = QHBoxLayout(self)
        controls_layout = QVBoxLayout()

        # ------------------
        # выбор файла
        # ------------------
        file_layout = QHBoxLayout()
        self.file_label = QLabel("CSV не выбран")
        self.load_btn = QPushButton("Загрузить CSV")
        self.load_btn.clicked.connect(self.load_file)

        file_layout.addWidget(self.load_btn)
        file_layout.addWidget(self.file_label)

        # ------------------
        # число кластеров
        # ------------------
        r_layout = QHBoxLayout()
        r_layout.addWidget(QLabel("Кластеров r:"))
        self.r_input = QSpinBox()
        self.r_input.setMinimum(2)
        self.r_input.setValue(2)
        self.r_input.valueChanged.connect(self._rebuild_partial_inputs)
        r_layout.addWidget(self.r_input)

        # ------------------
        # режим задания размеров
        # ------------------
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Режим размеров:"))

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("0 - не задавать", 0)
        self.mode_combo.addItem("1 - частично задать", 1)
        self.mode_combo.addItem("2 - равные кластеры", 2)
        self.mode_combo.currentIndexChanged.connect(self._toggle_partial_panel)
        mode_layout.addWidget(self.mode_combo)

        self.partial_group = QWidget()
        self.partial_form = QFormLayout(self.partial_group)
        self.partial_inputs = []
        self._rebuild_partial_inputs()

        # ------------------
        # запуск
        # ------------------
        self.solve_btn = QPushButton("Запустить расчет")
        self.solve_btn.clicked.connect(self.run_model)

        # ------------------
        # вывод
        # ------------------
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        controls_layout.addLayout(file_layout)
        controls_layout.addLayout(r_layout)
        controls_layout.addLayout(mode_layout)
        controls_layout.addWidget(self.partial_group)
        controls_layout.addWidget(self.solve_btn)
        controls_layout.addWidget(self.output)

        # ------------------
        # график в приложении
        # ------------------
        self.figure = Figure(figsize=(6, 5))
        self.canvas = FigureCanvas(self.figure)

        root_layout.addLayout(controls_layout, 2)
        root_layout.addWidget(self.canvas, 3)

        self._toggle_partial_panel()

    def _rebuild_partial_inputs(self):
        while self.partial_form.rowCount():
            self.partial_form.removeRow(0)

        self.partial_inputs = []
        r = self.r_input.value()

        for j in range(max(0, r - 1)):
            line_edit = QLineEdit()
            line_edit.setPlaceholderText("пусто = не задавать")
            self.partial_form.addRow(f"|P{j + 1}|:", line_edit)
            self.partial_inputs.append(line_edit)

    def _toggle_partial_panel(self):
        mode = self.mode_combo.currentData()
        self.partial_group.setVisible(mode == 1)

    def _build_cluster_sizes(self, n, r):
        mode = self.mode_combo.currentData()

        # 0 - не задавать
        if mode == 0:
            return None

        # 2 - равные
        if mode == 2:
            base = n // r
            sizes = [base] * r
            sizes[-1] = n - base * (r - 1)
            return sizes

        # 1 - частично
        sizes = [None] * r
        fixed_sum = 0

        for j, widget in enumerate(self.partial_inputs):
            text = widget.text().strip()
            if text == "":
                continue

            value = int(text)
            if value <= 0:
                raise ValueError("Размер кластера должен быть > 0")

            sizes[j] = value
            fixed_sum += value

        sizes[-1] = n - fixed_sum
        if sizes[-1] <= 0:
            raise ValueError(
                "Некорректное разбиение: последний кластер <= 0. "
                "Уменьшите фиксированные размеры."
            )

        return sizes

    def load_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Выбери CSV", "", "CSV Files (*.csv)"
        )

        if file_name:
            self.csv_path = file_name
            self.file_label.setText(file_name)

    def run_model(self):
        if not self.csv_path:
            QMessageBox.warning(self, "Ошибка", "Сначала выбери CSV")
            return

        try:
            self.output.clear()
            self.figure.clear()

            x, y = load_csv(self.csv_path)
            r = self.r_input.value()

            cluster_sizes = self._build_cluster_sizes(len(x), r)

            self.output.append("Строим MILP модель...")
            model = build_model(x, y, r, cluster_sizes)

            self.output.append("Решаем...")
            solve_model(model)

            results = extract_results(model, x, y, r)

            self.output.append("\n=== КЛАСТЕРЫ ===")
            for j, pts in results["clusters"].items():
                self.output.append(f"P{j + 1} = {[k + 1 for k in pts]}")

            self.output.append("\n=== МОДЕЛИ ===")
            for j, (a0, a1) in enumerate(results["coeffs"]):
                self.output.append(f"Кластер {j + 1}: y = {a0:.2f} + {a1:.2f}x")

            E = mean_percent_error(y, results["u"])
            self.output.append(f"\nE = {E:.4f}%")

            ax = self.figure.add_subplot(111)
            plot_clusters(results, x, y, ax=ax, show=False)
            self.canvas.draw()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))