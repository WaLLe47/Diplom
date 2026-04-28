from datetime import datetime
from tempfile import TemporaryDirectory

import numpy as np
from matplotlib import image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStyle,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from analysis.extract_results import extract_results
from analysis.metrics import mean_percent_error
from data.loader import load_csv
from model.build_model import build_model
from solver.solve_model import solve_model
from visualization.plot_clusters import build_cluster_plot, build_error_plot

DARK_THEME_QSS = """
QWidget {
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 14px;
    color: #f3f4f6;
    background: #050b16;
}
QGroupBox {
    border: 1px solid #f59e0b;
    border-radius: 14px;
    margin-top: 12px;
    padding-top: 18px;
    font-weight: 700;
    background: #111827;
    color: #f59e0b;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
}
QPushButton {
    min-height: 36px;
    border-radius: 12px;
    padding: 0 14px;
    background: #f59e0b;
    border: 1px solid #f59e0b;
    color: #111827;
    font-weight: 700;
}
QPushButton:hover { background: #fbbf24; }
QPushButton#primary { background-color: #f59e0b; color: #111827; }
QPushButton#theme_btn {
    background: #111827;
    color: #f59e0b;
    border: 1px solid #f59e0b;
}
QPushButton#theme_btn:hover { background: #1f2937; }
QTextEdit {
    border: 1px solid #374151;
    border-radius: 12px;
    background: #111827;
    color: #f9fafb;
    selection-background-color: #f59e0b;
}
QLineEdit, QSpinBox, QComboBox {
    background: #0f172a;
    border: 1px solid #374151;
    border-radius: 10px;
    min-height: 30px;
    color: #f9fafb;
    padding: 2px 6px;
}
QPushButton#mode_btn {
    min-height: 30px;
    border-radius: 10px;
    padding: 0 10px;
    font-size: 12px;
    font-weight: 600;
    background: #0f172a;
    color: #d1d5db;
    border: 1px solid #374151;
}
QPushButton#mode_btn:checked {
    background: #f59e0b;
    color: #111827;
    border: 1px solid #f59e0b;
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 20px;
    border-left: 1px solid #374151;
    background: #1f2937;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: #374151;
}
QSpinBox::up-arrow {
    width: 0px;
    height: 0px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 7px solid #f9fafb;
}
QSpinBox::down-arrow {
    width: 0px;
    height: 0px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 7px solid #f9fafb;
}
QTabWidget::pane {
    border: 1px solid #374151;
    border-radius: 12px;
    background: #111827;
}
QTabBar::tab {
    background: #111827;
    color: #d1d5db;
    padding: 10px 16px;
    border: 1px solid #374151;
    border-bottom: 0px;
    margin-right: 2px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}
QTabBar::tab:selected {
    background: #f59e0b;
    color: #111827;
    border-color: #f59e0b;
}
QLabel#muted { color: #d1d5db; }
"""

LIGHT_THEME_QSS = """
QWidget {
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 14px;
    color: #111827;
    background: #f3f4f6;
}
QGroupBox {
    border: 1px solid #ea580c;
    border-radius: 14px;
    margin-top: 12px;
    padding-top: 18px;
    font-weight: 700;
    background: #ffffff;
    color: #ea580c;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
}
QPushButton {
    min-height: 36px;
    border-radius: 12px;
    padding: 0 14px;
    background: #ea580c;
    border: 1px solid #ea580c;
    color: #ffffff;
    font-weight: 700;
}
QPushButton:hover { background: #fb923c; }
QPushButton#primary { background-color: #ea580c; color: #ffffff; }
QPushButton#theme_btn {
    background: #ffffff;
    color: #ea580c;
    border: 1px solid #ea580c;
}
QPushButton#theme_btn:hover { background: #fff7ed; }
QTextEdit {
    border: 1px solid #9ca3af;
    border-radius: 12px;
    background: #ffffff;
    color: #111827;
    selection-background-color: #fb923c;
}
QLineEdit, QSpinBox, QComboBox {
    background: #ffffff;
    border: 1px solid #9ca3af;
    border-radius: 10px;
    min-height: 30px;
    color: #111827;
    padding: 2px 6px;
}
QPushButton#mode_btn {
    min-height: 30px;
    border-radius: 10px;
    padding: 0 10px;
    font-size: 12px;
    font-weight: 600;
    background: #ffffff;
    color: #374151;
    border: 1px solid #9ca3af;
}
QPushButton#mode_btn:checked {
    background: #ea580c;
    color: #ffffff;
    border: 1px solid #ea580c;
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 20px;
    border-left: 1px solid #9ca3af;
    background: #f3f4f6;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: #e5e7eb;
}
QSpinBox::up-arrow {
    width: 0px;
    height: 0px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 7px solid #1f2937;
}
QSpinBox::down-arrow {
    width: 0px;
    height: 0px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 7px solid #1f2937;
}
QTabWidget::pane {
    border: 1px solid #9ca3af;
    border-radius: 12px;
    background: #ffffff;
}
QTabBar::tab {
    background: #ffffff;
    color: #374151;
    padding: 10px 16px;
    border: 1px solid #9ca3af;
    border-bottom: 0px;
    margin-right: 2px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}
QTabBar::tab:selected {
    background: #ea580c;
    color: #ffffff;
    border-color: #ea580c;
}
QLabel#muted { color: #374151; }
"""


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.csv_path = None
        self.last_results = None
        self.last_x = None
        self.last_y = None
        self.last_global_coeffs = None
        self.last_cluster_fig = None
        self.last_error_fig = None
        self.current_theme = "dark"

        self.setWindowTitle("Cluster Regression MILP")
        self.resize(1240, 800)

        root_layout = QHBoxLayout(self)
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(10)

        file_group = QGroupBox("Данные")
        file_layout = QHBoxLayout(file_group)

        self.file_label = QLabel("CSV не выбран")
        self.file_label.setWordWrap(True)
        self.file_label.setObjectName("muted")

        self.load_btn = QPushButton("Загрузить CSV")
        self.load_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        self.load_btn.clicked.connect(self.load_file)

        file_layout.addWidget(self.load_btn)
        file_layout.addWidget(self.file_label, 1)

        params_group = QGroupBox("Параметры")
        params_layout = QVBoxLayout(params_group)

        r_layout = QHBoxLayout()
        r_layout.addWidget(QLabel("Кластеров r:"))

        self.r_input = QSpinBox()
        self.r_input.setMinimum(2)
        self.r_input.setMaximum(50)
        self.r_input.setSingleStep(1)
        self.r_input.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        self.r_input.setValue(2)
        self.r_input.valueChanged.connect(self._rebuild_partial_inputs)
        r_layout.addWidget(self.r_input)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Режим размеров:"))

        self.mode_group = QButtonGroup(self)
        self.mode_none_btn = QPushButton("Не задавать")
        self.mode_none_btn.setObjectName("mode_btn")
        self.mode_none_btn.setCheckable(True)
        self.mode_partial_btn = QPushButton("Частично задать")
        self.mode_partial_btn.setObjectName("mode_btn")
        self.mode_partial_btn.setCheckable(True)
        self.mode_equal_btn = QPushButton("Равные кластеры")
        self.mode_equal_btn.setObjectName("mode_btn")
        self.mode_equal_btn.setCheckable(True)

        self.mode_group.addButton(self.mode_none_btn, 0)
        self.mode_group.addButton(self.mode_partial_btn, 1)
        self.mode_group.addButton(self.mode_equal_btn, 2)
        self.mode_none_btn.setChecked(True)
        self.mode_group.idClicked.connect(self._toggle_partial_panel)

        mode_layout.addWidget(self.mode_none_btn)
        mode_layout.addWidget(self.mode_partial_btn)
        mode_layout.addWidget(self.mode_equal_btn)

        self.partial_group = QWidget()
        self.partial_form = QFormLayout(self.partial_group)
        self.partial_inputs = []
        self._rebuild_partial_inputs()

        params_layout.addLayout(r_layout)
        params_layout.addLayout(mode_layout)
        params_layout.addWidget(self.partial_group)

        actions_group = QGroupBox("Действия")
        actions_layout = QHBoxLayout(actions_group)

        self.solve_btn = QPushButton("Запустить расчёт")
        self.solve_btn.setObjectName("primary")
        self.solve_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.solve_btn.clicked.connect(self.run_model)

        self.export_pdf_btn = QPushButton("Экспорт PDF")
        self.export_pdf_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DriveHDIcon))
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        self.export_pdf_btn.setEnabled(False)
        self.theme_btn = QPushButton("◉ СВЕТЛАЯ")
        self.theme_btn.setObjectName("theme_btn")
        self.theme_btn.clicked.connect(self.toggle_theme)

        actions_layout.addWidget(self.solve_btn)
        actions_layout.addWidget(self.export_pdf_btn)

        output_group = QGroupBox("Результаты")
        output_layout = QVBoxLayout(output_group)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("После расчёта здесь появится отчёт...")
        self.output.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        output_layout.addWidget(self.output)

        controls_layout.addWidget(file_group)
        controls_layout.addWidget(params_group)
        controls_layout.addWidget(actions_group)
        controls_layout.addWidget(output_group, 1)

        chart_group = QGroupBox("Графики")
        chart_layout = QVBoxLayout(chart_group)

        self.plot_tabs = QTabWidget()
        self.cluster_plot_view = QWebEngineView()
        self.error_plot_view = QWebEngineView()
        self.plot_tabs.addTab(self.cluster_plot_view, "Кластеры")
        self.plot_tabs.addTab(self.error_plot_view, "Ошибки")
        self.plot_tabs.setCornerWidget(self.theme_btn, Qt.Corner.TopRightCorner)

        chart_layout.addWidget(self.plot_tabs)

        root_layout.addLayout(controls_layout, 2)
        root_layout.addWidget(chart_group, 3)

        self._toggle_partial_panel()
        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet(DARK_THEME_QSS if self.current_theme == "dark" else LIGHT_THEME_QSS)
        self.setWindowIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.theme_btn.setText("◉ СВЕТЛАЯ" if self.current_theme == "dark" else "◉ ТЁМНАЯ")

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self._apply_styles()

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

    def _selected_mode(self):
        mode_id = self.mode_group.checkedId()
        return 0 if mode_id == -1 else mode_id

    def _toggle_partial_panel(self, *_):
        self.partial_group.setVisible(self._selected_mode() == 1)

    def _build_cluster_sizes(self, n, r):
        mode = self._selected_mode()

        if mode == 0:
            return None

        if mode == 2:
            base = n // r
            sizes = [base] * r
            sizes[-1] = n - base * (r - 1)
            return sizes

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

    def _format_points(self, points, chunk=12):
        if not points:
            return "[]"

        rows = []
        for i in range(0, len(points), chunk):
            rows.append(", ".join(str(v) for v in points[i : i + chunk]))
        return "[\n  " + ",\n  ".join(rows) + "\n]"

    def _render_plotly(self, cluster_fig, error_fig):
        config = {"scrollZoom": True, "displayModeBar": True}
        self.cluster_plot_view.setHtml(cluster_fig.to_html(include_plotlyjs="cdn", config=config))
        self.error_plot_view.setHtml(error_fig.to_html(include_plotlyjs="cdn", config=config))

    def _global_regression(self, x, y):
        slope, intercept = np.polyfit(np.asarray(x), np.asarray(y), 1)
        return intercept, slope

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

            x, y = load_csv(self.csv_path)
            r = self.r_input.value()

            cluster_sizes = self._build_cluster_sizes(len(x), r)

            self.output.append("Строим MILP модель...")
            model = build_model(x, y, r, cluster_sizes)

            self.output.append("Решаем...")
            solve_model(model)

            results = extract_results(model, x, y, r)
            g0, g1 = self._global_regression(x, y)

            self.output.append("\n=== КЛАСТЕРЫ ===")
            for j, pts in results["clusters"].items():
                self.output.append(f"P{j + 1} = {self._format_points([k + 1 for k in pts])}")

            self.output.append("\n=== ОБЩАЯ ФУНКЦИЯ ===")
            self.output.append(f"y = {g0:.2f} + {g1:.2f}x")

            self.output.append("\n=== КЛАСТЕРНЫЕ РЕГРЕССИИ ===")
            for j, (a0, a1) in enumerate(results["coeffs"]):
                self.output.append(f"Кластер {j + 1}: y = {a0:.2f} + {a1:.2f}x")

            self.output.append("\n=== ПОТОЧЕЧНЫЕ ОШИБКИ ===")
            for k, e in enumerate(results["u"], start=1):
                self.output.append(f"{k}: {e:.2f}")

            E = mean_percent_error(y, results["u"])
            self.output.append("\n=== СРЕДНЯЯ ПРОЦЕНТНАЯ ОШИБКА ===")
            self.output.append(f"E = {E:.4f}%")

            cluster_fig = build_cluster_plot(results, x, y, (g0, g1))
            error_fig = build_error_plot(results, x, y)
            self._render_plotly(cluster_fig, error_fig)

            self.last_results = results
            self.last_x = x
            self.last_y = y
            self.last_global_coeffs = (g0, g1)
            self.last_cluster_fig = cluster_fig
            self.last_error_fig = error_fig

            self.export_pdf_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def export_pdf(self):
        if self.last_results is None:
            QMessageBox.information(self, "PDF", "Сначала выполните расчёт.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчёт в PDF",
            f"cluster_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Files (*.pdf)",
        )

        if not file_path:
            return

        if not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"

        try:
            with TemporaryDirectory() as tmp_dir:
                p1 = f"{tmp_dir}/cluster_plot.png"
                p2 = f"{tmp_dir}/error_plot.png"

                self.last_cluster_fig.write_image(p1, width=1400, height=900, scale=2)
                self.last_error_fig.write_image(p2, width=1400, height=900, scale=2)

                with PdfPages(file_path) as pdf:
                    text_fig = Figure(figsize=(8.27, 11.69))
                    text_ax = text_fig.add_subplot(111)
                    text_ax.axis("off")
                    report_lines = [
                        "ОТЧЁТ ПО КЛАСТЕРНОЙ РЕГРЕССИИ",
                        f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                        "",
                        self.output.toPlainText(),
                    ]
                    text_ax.text(
                        0.02,
                        0.98,
                        "\n".join(report_lines),
                        va="top",
                        ha="left",
                        fontsize=9,
                        family="monospace",
                        wrap=True,
                    )
                    pdf.savefig(text_fig)

                    cluster_img = mpimg.imread(p1)
                    fig_cluster = Figure(figsize=(11.69, 8.27))
                    ax_cluster = fig_cluster.add_subplot(111)
                    ax_cluster.axis("off")
                    ax_cluster.imshow(cluster_img)
                    pdf.savefig(fig_cluster)

                    error_img = mpimg.imread(p2)
                    fig_error = Figure(figsize=(11.69, 8.27))
                    ax_error = fig_error.add_subplot(111)
                    ax_error.axis("off")
                    ax_error.imshow(error_img)
                    pdf.savefig(fig_error)

            QMessageBox.information(self, "PDF", f"Отчёт сохранён:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "PDF",
                f"Ошибка при сохранении PDF:\n{e}\n\n"
                "Убедитесь, что установлен kaleido: pip install kaleido",
            )