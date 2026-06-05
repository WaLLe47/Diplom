"""Main Qt window for the MILP cluster regression application."""

import tempfile
from datetime import datetime
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import numpy as np
import qdarktheme
from matplotlib import image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStyle,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from analysis.extract_results import extract_results
from analysis.metrics import mean_percent_error
from data.loader import load_csv
from model.build_model import build_model
from solver.solve_model import solve_model
from visualization.plot_clusters import build_cluster_plot, build_error_plot

RUN_BUTTON_TEXT = " ЗАПУСТИТЬ РАСЧЁТ"
DRAWER_WIDTH = 360


class DataPreviewDialog(QDialog):
    """Modal window that shows the CSV data selected by the user."""

    def __init__(self, file_path: str, x: list[float], y: list[float], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Загруженные данные")
        self.resize(560, 520)

        layout = QVBoxLayout(self)
        file_label = QLabel(f"Файл: {Path(file_path).name}")
        rows_label = QLabel(f"Загружено наблюдений: {len(x)}")

        self.table = QTableWidget(len(x), 3)
        self.table.setHorizontalHeaderLabels(["№", "x", "y"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for row_index, (x_value, y_value) in enumerate(zip(x, y), start=1):
            index_item = QTableWidgetItem(str(row_index))
            index_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_index - 1, 0, index_item)
            self.table.setItem(row_index - 1, 1, QTableWidgetItem(str(x_value)))
            self.table.setItem(row_index - 1, 2, QTableWidgetItem(str(y_value)))

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)

        layout.addWidget(file_label)
        layout.addWidget(rows_label)
        layout.addWidget(self.table, 1)
        layout.addWidget(close_button)


class SolverThread(QThread):
    """Run MILP solving outside the UI thread."""

    finished = Signal(dict, tuple)
    error = Signal(str)

    def __init__(
        self,
        x: list[float],
        y: list[float],
        r: int,
        cluster_sizes: list[int | None] | None,
    ) -> None:
        super().__init__()
        self.x = x
        self.y = y
        self.r = r
        self.cluster_sizes = cluster_sizes

    def run(self) -> None:
        try:
            model = build_model(self.x, self.y, self.r, self.cluster_sizes)
            solve_model(model)
            results = extract_results(model, self.x, self.y, self.r)
            slope, intercept = np.polyfit(np.asarray(self.x), np.asarray(self.y), 1)
            self.finished.emit(results, (float(intercept), float(slope)))
        except Exception as error:
            self.error.emit(str(error))


class MainWindow(QWidget):
    """Top-level application widget."""

    def __init__(self) -> None:
        super().__init__()
        self.csv_path: str | None = None
        self.loaded_data: tuple[list[float], list[float]] | None = None
        self.last_results: dict[str, Any] | None = None
        self.current_data: tuple[list[float], list[float], int] | None = None
        self.g_coeffs: tuple[float, float] | None = None
        self.worker: SolverThread | None = None
        self.partial_inputs: list[QLineEdit] = []
        self.current_theme = "dark"
        self.drawer_visible = True

        self.setStyleSheet(qdarktheme.load_stylesheet(self.current_theme))
        self.setWindowTitle("MILP Cluster Analysis Pro")
        self.resize(1400, 860)

        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self._build_menu_rail())
        main_layout.addWidget(self._build_side_drawer())
        main_layout.addLayout(self._build_charts_panel(), 1)

    def _build_menu_rail(self) -> QWidget:
        rail = QWidget()
        rail.setFixedWidth(52)
        rail.setObjectName("menuRail")
        rail_layout = QVBoxLayout(rail)
        rail_layout.setContentsMargins(6, 8, 6, 8)

        self.drawer_toggle_btn = QPushButton("☰")
        self.drawer_toggle_btn.setToolTip("Показать/скрыть боковое меню")
        self.drawer_toggle_btn.setMinimumHeight(40)
        self.drawer_toggle_btn.clicked.connect(self.toggle_drawer)

        rail_layout.addWidget(self.drawer_toggle_btn)
        rail_layout.addStretch(1)
        return rail

    def _build_side_drawer(self) -> QWidget:
        self.side_drawer = QWidget()
        self.side_drawer.setObjectName("sideDrawer")
        self.side_drawer.setFixedWidth(DRAWER_WIDTH)

        drawer_layout = QVBoxLayout(self.side_drawer)
        drawer_layout.setContentsMargins(14, 14, 14, 14)
        drawer_layout.setSpacing(12)

        title = QLabel("Меню")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        drawer_layout.addWidget(title)
        drawer_layout.addWidget(self._build_data_group())
        drawer_layout.addWidget(self._build_params_group())
        drawer_layout.addWidget(self._build_action_group())
        drawer_layout.addWidget(self._build_results_group(), 1)

        return self.side_drawer

    def _build_data_group(self) -> QGroupBox:
        data_group = QGroupBox("1. Данные")
        data_layout = QVBoxLayout(data_group)
        data_layout.setSpacing(8)

        self.load_btn = QPushButton(" Выбрать CSV")
        self.load_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.load_btn.clicked.connect(self.load_file)

        self.preview_btn = QPushButton(" Показать данные")
        self.preview_btn.setEnabled(False)
        self.preview_btn.clicked.connect(self.show_loaded_data)

        self.file_info = QLabel("Файл не загружен")
        self.file_info.setWordWrap(True)
        self.file_info.setStyleSheet("opacity: 0.75;")

        data_layout.addWidget(self.load_btn)
        data_layout.addWidget(self.preview_btn)
        data_layout.addWidget(self.file_info)
        return data_group

    def _build_params_group(self) -> QGroupBox:
        params_group = QGroupBox("2. Настройки модели")
        params_layout = QFormLayout(params_group)
        params_layout.setVerticalSpacing(10)

        self.r_input = QSpinBox()
        self.r_input.setRange(2, 50)
        self.r_input.setValue(2)
        self.r_input.valueChanged.connect(self._rebuild_partial_inputs)
        params_layout.addRow("Кластеры (r):", self.r_input)

        self.mode_combo = QButtonGroup(self)
        mode_hbox = QHBoxLayout()
        mode_hbox.setSpacing(6)
        for mode_id, text in enumerate(["Свободно", "Вручную", "Поровну"]):
            button = QPushButton(text)
            button.setCheckable(True)
            button.setChecked(mode_id == 0)
            self.mode_combo.addButton(button, mode_id)
            mode_hbox.addWidget(button)
        self.mode_combo.idClicked.connect(self._toggle_partial_panel)
        params_layout.addRow("Размеры:", mode_hbox)

        self.partial_container = QWidget()
        self.partial_form = QFormLayout(self.partial_container)
        self.partial_form.setContentsMargins(0, 0, 0, 0)
        self.partial_form.setVerticalSpacing(8)
        self._rebuild_partial_inputs()
        params_layout.addRow(self.partial_container)

        return params_group

    def _build_action_group(self) -> QGroupBox:
        action_group = QGroupBox("3. Действия")
        action_layout = QVBoxLayout(action_group)
        action_layout.setSpacing(8)

        self.solve_btn = QPushButton(RUN_BUTTON_TEXT)
        self.solve_btn.setMinimumHeight(38)
        self.solve_btn.setStyleSheet(
            "background-color: #0284c7; color: white; font-weight: bold; border-radius: 6px;"
        )
        self.solve_btn.clicked.connect(self.run_model)

        self.pdf_btn = QPushButton(" Экспорт PDF")
        self.pdf_btn.setMinimumHeight(34)
        self.pdf_btn.setEnabled(False)
        self.pdf_btn.clicked.connect(self.export_pdf)

        self.theme_btn = QPushButton(" Сменить тему")
        self.theme_btn.setMinimumHeight(34)
        self.theme_btn.clicked.connect(self.toggle_theme)

        action_layout.addWidget(self.solve_btn)
        action_layout.addWidget(self.pdf_btn)
        action_layout.addWidget(self.theme_btn)
        return action_group

    def _build_results_group(self) -> QGroupBox:
        results_group = QGroupBox("4. Результаты MILP")
        results_layout = QVBoxLayout(results_group)

        self.metrics_lbl = QLabel("Ожидание запуска...")
        self.metrics_lbl.setWordWrap(True)
        self.metrics_lbl.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #0284c7; margin-bottom: 2px;"
        )

        self.global_reg_lbl = QLabel("")
        self.global_reg_lbl.setWordWrap(True)
        self.global_reg_lbl.setStyleSheet("font-size: 13px; margin-bottom: 8px;")

        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Кластер", "Уравнение", "Точек"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.verticalHeader().setDefaultSectionSize(32)

        self.details_browser = QTextBrowser()
        self.details_browser.setPlaceholderText("Здесь будет детализация распределения точек...")

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.results_table)
        splitter.addWidget(self.details_browser)
        splitter.setSizes([180, 220])

        results_layout.addWidget(self.metrics_lbl)
        results_layout.addWidget(self.global_reg_lbl)
        results_layout.addWidget(splitter, 1)
        return results_group

    def _build_charts_panel(self) -> QVBoxLayout:
        from PySide6.QtWebEngineWidgets import QWebEngineView

        charts_panel = QVBoxLayout()
        charts_panel.setContentsMargins(12, 12, 12, 12)
        self.tabs = QTabWidget()
        self.view_cluster = QWebEngineView()
        self.view_error = QWebEngineView()
        self.tabs.addTab(self.view_cluster, "Кластерная модель")
        self.tabs.addTab(self.view_error, "Ошибки и отклонения")
        charts_panel.addWidget(self.tabs)
        return charts_panel

    def toggle_drawer(self) -> None:
        self.drawer_visible = not self.drawer_visible
        self.side_drawer.setVisible(self.drawer_visible)
        self.drawer_toggle_btn.setText("☰" if self.drawer_visible else "›")
        self.drawer_toggle_btn.setToolTip(
            "Скрыть боковое меню" if self.drawer_visible else "Показать боковое меню"
        )

    def toggle_theme(self) -> None:
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.setStyleSheet(qdarktheme.load_stylesheet(self.current_theme))
        if self.last_results:
            self._render_details_html()

    def load_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Открыть данные", "", "CSV (*.csv)")
        if not path:
            return

        try:
            x, y = load_csv(path)
        except Exception as error:
            QMessageBox.critical(self, "Ошибка загрузки", str(error))
            return

        self.csv_path = path
        self.loaded_data = (x, y)
        self.current_data = None
        self.last_results = None
        self.g_coeffs = None
        self.file_info.setText(f"{Path(path).name}\n{len(x)} наблюдений")
        self.preview_btn.setEnabled(True)
        self.pdf_btn.setEnabled(False)
        self.metrics_lbl.setText("Данные загружены. Можно запускать расчёт.")
        self.global_reg_lbl.setText("")
        self.results_table.setRowCount(0)
        self.details_browser.clear()
        self.show_loaded_data()

    def show_loaded_data(self) -> None:
        if self.csv_path is None or self.loaded_data is None:
            QMessageBox.warning(self, "Внимание", "Сначала загрузите CSV файл.")
            return

        x, y = self.loaded_data
        DataPreviewDialog(self.csv_path, x, y, self).exec()

    def _rebuild_partial_inputs(self) -> None:
        while self.partial_form.count():
            child = self.partial_form.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.partial_inputs = []
        for index in range(self.r_input.value() - 1):
            edit = QLineEdit()
            edit.setPlaceholderText("Кол-во (или пусто)")
            self.partial_form.addRow(f"|P{index + 1}|:", edit)
            self.partial_inputs.append(edit)
        self._toggle_partial_panel()

    def _toggle_partial_panel(self, *_args: object) -> None:
        self.partial_container.setVisible(self.mode_combo.checkedId() == 1)

    def run_model(self) -> None:
        if self.loaded_data is None:
            QMessageBox.warning(self, "Внимание", "Сначала загрузите CSV файл.")
            return

        try:
            x, y = self.loaded_data
            r = self.r_input.value()
            sizes = self._build_sizes(len(x), r)

            self._set_solving_state(True)
            self.current_data = (x, y, r)
            self.worker = SolverThread(x, y, r, sizes)
            self.worker.finished.connect(self._on_success)
            self.worker.error.connect(self._on_error)
            self.worker.start()
        except Exception as error:
            self._set_solving_state(False)
            QMessageBox.critical(self, "Ошибка", str(error))

    def _set_solving_state(self, is_solving: bool) -> None:
        self.solve_btn.setEnabled(not is_solving)
        self.solve_btn.setText("РАСЧЁТ В ПРОЦЕССЕ..." if is_solving else RUN_BUTTON_TEXT)

        if is_solving:
            self.pdf_btn.setEnabled(False)
            self.metrics_lbl.setText("⏳ Идет построение MILP модели...")
            self.global_reg_lbl.setText("")
            self.results_table.setRowCount(0)
            self.details_browser.clear()

    def _on_error(self, error_message: str) -> None:
        self._set_solving_state(False)
        self.metrics_lbl.setText("❌ Ошибка при расчёте")
        QMessageBox.critical(self, "Ошибка", error_message)

    def _on_success(self, results: dict[str, Any], global_coeffs: tuple[float, float]) -> None:
        self._set_solving_state(False)
        self.last_results = results
        self.g_coeffs = global_coeffs

        if self.current_data is None:
            return

        x, y, r = self.current_data
        self._fill_results_table(results, r)
        self._render_details_html()
        self._render_metrics(y, results, global_coeffs)
        self._render_plots(
            build_cluster_plot(results, x, y, global_coeffs),
            build_error_plot(results, x, y),
        )
        self.pdf_btn.setEnabled(True)

    def _fill_results_table(self, results: dict[str, Any], r: int) -> None:
        self.results_table.setRowCount(r)
        for index, (a0, a1) in enumerate(results["coeffs"]):
            cluster_points = results["clusters"].get(index, [])

            item_cluster = QTableWidgetItem(f"P{index + 1}")
            item_cluster.setTextAlignment(Qt.AlignCenter)
            self.results_table.setItem(index, 0, item_cluster)

            self.results_table.setItem(index, 1, QTableWidgetItem(f"{a0:.3f} + {a1:.3f}*x"))

            item_points = QTableWidgetItem(str(len(cluster_points)))
            item_points.setTextAlignment(Qt.AlignCenter)
            self.results_table.setItem(index, 2, item_points)

    def _render_metrics(
        self,
        y: list[float],
        results: dict[str, Any],
        global_coeffs: tuple[float, float],
    ) -> None:
        g0, g1 = global_coeffs
        error_value = mean_percent_error(y, results["u"])
        self.metrics_lbl.setText(f"Средняя ошибка (E): {error_value:.4f}%")
        self.global_reg_lbl.setText(f"Общая регрессия: y = {g0:.4f} + {g1:.4f} * x")

    def _render_details_html(self) -> None:
        if self.last_results is None:
            return

        is_dark = self.current_theme == "dark"
        text_color = "#e8eaed" if is_dark else "#202124"
        accent_color = "#8ab4f8" if is_dark else "#1a73e8"
        muted_color = "#9aa0a6" if is_dark else "#5f6368"
        border_color = "#3c4043" if is_dark else "#dadce0"

        html_parts = [
            f"<div style='font-family: sans-serif; font-size: 14px; color: {text_color}; line-height: 1.5;'>",
            f"<h3 style='color: {accent_color}; border-bottom: 1px solid {border_color}; padding-bottom: 5px; margin-top: 0;'>Детализация кластеров:</h3>",
        ]

        for index in range(len(self.last_results["coeffs"])):
            point_numbers = [str(point + 1) for point in self.last_results["clusters"].get(index, [])]
            html_parts.extend(
                [
                    "<p style='margin-bottom: 8px;'>",
                    f"<b style='color: {accent_color};'>P{index + 1}:</b> ",
                    f"<span style='color: {muted_color}; font-family: monospace;'>[{escape(', '.join(point_numbers))}]</span>",
                    "</p>",
                ]
            )

        html_parts.append("</div>")
        self.details_browser.setHtml("".join(html_parts))

    def _render_plots(self, cluster_fig, error_fig) -> None:
        temp_dir = Path(tempfile.gettempdir())
        cluster_path = temp_dir / "p1_cluster.html"
        error_path = temp_dir / "p2_error.html"
        config = {"scrollZoom": True, "displayModeBar": True}

        cluster_fig.write_html(cluster_path, include_plotlyjs=True, config=config)
        error_fig.write_html(error_path, include_plotlyjs=True, config=config)
        self.view_cluster.load(QUrl.fromLocalFile(str(cluster_path)))
        self.view_error.load(QUrl.fromLocalFile(str(error_path)))

    def _build_sizes(self, n: int, r: int) -> list[int | None] | None:
        mode = self.mode_combo.checkedId()
        if mode == 0:
            return None
        if mode == 2:
            base_size = n // r
            sizes = [base_size] * r
            sizes[-1] = n - base_size * (r - 1)
            return sizes

        sizes: list[int | None] = [None] * r
        fixed_sum = 0
        for index, edit in enumerate(self.partial_inputs):
            raw_value = edit.text().strip()
            if not raw_value:
                continue

            size = int(raw_value)
            if size < 0:
                raise ValueError("Размеры кластеров не могут быть отрицательными")
            sizes[index] = size
            fixed_sum += size

        sizes[-1] = n - fixed_sum
        if sizes[-1] <= 0:
            raise ValueError("Некорректное разбиение: последний кластер <= 0")
        return sizes

    def export_pdf(self) -> None:
        if self.last_results is None or self.current_data is None or self.g_coeffs is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчёт в PDF",
            f"cluster_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Files (*.pdf)",
        )
        if not file_path:
            return

        output_path = Path(file_path)
        if output_path.suffix.lower() != ".pdf":
            output_path = output_path.with_suffix(".pdf")

        try:
            self._write_pdf(output_path)
            QMessageBox.information(self, "PDF", f"Отчёт успешно сохранён:\n{output_path}")
        except Exception as error:
            QMessageBox.critical(self, "PDF", f"Ошибка сохранения PDF:\n{error}")

    def _write_pdf(self, output_path: Path) -> None:
        if self.last_results is None or self.current_data is None or self.g_coeffs is None:
            return

        x, y, _r = self.current_data
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            cluster_png = tmp_path / "cluster_plot.png"
            error_png = tmp_path / "error_plot.png"

            build_cluster_plot(self.last_results, x, y, self.g_coeffs).write_image(
                cluster_png,
                width=1400,
                height=900,
                scale=2,
            )
            build_error_plot(self.last_results, x, y).write_image(
                error_png,
                width=1400,
                height=900,
                scale=2,
            )

            with PdfPages(output_path) as pdf:
                self._append_summary_page(pdf)
                self._append_image_page(pdf, cluster_png)
                self._append_image_page(pdf, error_png)

    def _append_summary_page(self, pdf: PdfPages) -> None:
        if self.last_results is None or self.current_data is None or self.g_coeffs is None:
            return

        _x, y, _r = self.current_data
        g0, g1 = self.g_coeffs
        error_value = mean_percent_error(y, self.last_results["u"])
        report_lines = [
            "ОТЧЁТ ПО КЛАСТЕРНОЙ РЕГРЕССИИ",
            f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
            "",
            f"Средняя ошибка (E): {error_value:.4f}%",
            f"Общая регрессия: y = {g0:.4f} + {g1:.4f} * x",
            "",
            "УРАВНЕНИЯ И РАСПРЕДЕЛЕНИЕ КЛАСТЕРОВ:",
        ]

        for index, (a0, a1) in enumerate(self.last_results["coeffs"]):
            points = self.last_results["clusters"].get(index, [])
            point_numbers = ", ".join(str(point + 1) for point in points)
            report_lines.append(f"P{index + 1}: y = {a0:.4f} + {a1:.4f}*x")
            report_lines.append(f"    Точек ({len(points)}): [{point_numbers}]")

        figure = Figure(figsize=(8.27, 11.69))
        axis = figure.add_subplot(111)
        axis.axis("off")
        axis.text(
            0.02,
            0.98,
            "\n".join(report_lines),
            va="top",
            ha="left",
            fontsize=10,
            family="monospace",
            wrap=True,
        )
        pdf.savefig(figure)

    @staticmethod
    def _append_image_page(pdf: PdfPages, image_path: Path) -> None:
        image = mpimg.imread(image_path)
        figure = Figure(figsize=(11.69, 8.27))
        axis = figure.add_subplot(111)
        axis.axis("off")
        axis.imshow(image)
        pdf.savefig(figure)