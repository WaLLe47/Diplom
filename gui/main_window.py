import os
import tempfile
from datetime import datetime
from tempfile import TemporaryDirectory

import numpy as np
from matplotlib import image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QButtonGroup, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QStyle,
    QTabWidget, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QTextBrowser, QSplitter
)
import qdarktheme

from analysis.extract_results import extract_results
from analysis.metrics import mean_percent_error
from data.loader import load_csv
from model.build_model import build_model
from solver.solve_model import solve_model
from visualization.plot_clusters import build_cluster_plot, build_error_plot


class SolverThread(QThread):
    finished = Signal(dict, tuple)
    error = Signal(str)

    def __init__(self, x, y, r, cluster_sizes):
        super().__init__()
        self.x = x
        self.y = y
        self.r = r
        self.cluster_sizes = cluster_sizes

    def run(self):
        try:
            model = build_model(self.x, self.y, self.r, self.cluster_sizes)
            solve_model(model)
            results = extract_results(model, self.x, self.y, self.r)
            slope, intercept = np.polyfit(np.asarray(self.x), np.asarray(self.y), 1)
            self.finished.emit(results, (intercept, slope))
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.csv_path = None
        self.last_results = None
        self.current_data = None
        self.g_coeffs = None

        # Устанавливаем тему по умолчанию через qdarktheme
        self.current_theme = "dark"
        self.setStyleSheet(qdarktheme.load_stylesheet(self.current_theme))

        self.setWindowTitle("MILP Cluster Analysis Pro")
        self.resize(1300, 850)

        main_layout = QHBoxLayout(self)
        left_panel = QVBoxLayout()
        left_panel.setSpacing(14)

        # --- 1. ГРУППА ДАННЫХ ---
        data_group = QGroupBox("1. Источник данных")
        data_layout = QHBoxLayout(data_group)
        self.load_btn = QPushButton(" Выбрать CSV")
        self.load_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.load_btn.clicked.connect(self.load_file)
        self.file_info = QLabel("Файл не загружен")
        # Используем полупрозрачность для текста "нет файла", чтобы он смотрелся хорошо в любой теме
        self.file_info.setStyleSheet("opacity: 0.6;")
        data_layout.addWidget(self.load_btn)
        data_layout.addWidget(self.file_info, 1)

        # --- 2. ГРУППА НАСТРОЕК ---
        params_group = QGroupBox("2. Настройки модели")
        params_layout = QFormLayout(params_group)
        params_layout.setVerticalSpacing(12)

        self.r_input = QSpinBox()
        self.r_input.setRange(2, 50)
        self.r_input.setValue(2)
        # Теперь кнопки 100% работают!
        self.r_input.valueChanged.connect(self._rebuild_partial_inputs)
        params_layout.addRow("Число кластеров (r):", self.r_input)

        self.mode_combo = QButtonGroup(self)
        mode_hbox = QHBoxLayout()
        mode_hbox.setSpacing(6)
        for i, text in enumerate(["Свободно", "Вручную", "Поровну"]):
            btn = QPushButton(text)
            btn.setCheckable(True)
            if i == 0: btn.setChecked(True)
            self.mode_combo.addButton(btn, i)
            mode_hbox.addWidget(btn)
        self.mode_combo.idClicked.connect(self._toggle_partial_panel)
        params_layout.addRow("Режим размеров:", mode_hbox)

        self.partial_container = QWidget()
        self.partial_form = QFormLayout(self.partial_container)
        self.partial_form.setContentsMargins(0, 0, 0, 0)
        self.partial_form.setVerticalSpacing(8)
        self.partial_inputs = []
        self._rebuild_partial_inputs()
        params_layout.addRow(self.partial_container)

        # --- 3. ГРУППА ДЕЙСТВИЙ ---
        action_group = QGroupBox("3. Управление")
        action_layout = QHBoxLayout(action_group)

        self.solve_btn = QPushButton(" ЗАПУСТИТЬ РАСЧЁТ")
        self.solve_btn.setMinimumHeight(38)
        # Принудительно задаем акцентный цвет для главной кнопки
        self.solve_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; border-radius: 6px;")
        self.solve_btn.clicked.connect(self.run_model)

        self.pdf_btn = QPushButton(" Экспорт PDF")
        self.pdf_btn.setMinimumHeight(38)
        self.pdf_btn.setEnabled(False)
        self.pdf_btn.clicked.connect(self.export_pdf)

        self.theme_btn = QPushButton(" Сменить тему")
        self.theme_btn.setMinimumHeight(38)
        self.theme_btn.clicked.connect(self.toggle_theme)

        action_layout.addWidget(self.solve_btn, 2)
        action_layout.addWidget(self.pdf_btn, 1)
        action_layout.addWidget(self.theme_btn, 1)

        # --- 4. ГРУППА РЕЗУЛЬТАТОВ ---
        res_group = QGroupBox("4. Результаты MILP")
        res_layout = QVBoxLayout(res_group)

        self.metrics_lbl = QLabel("Ожидание запуска...")
        self.metrics_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #0284c7; margin-bottom: 2px;")

        self.global_reg_lbl = QLabel("")
        self.global_reg_lbl.setStyleSheet("font-size: 14px; margin-bottom: 8px;")

        self.res_splitter = QSplitter(Qt.Vertical)

        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Кластер", "Уравнение (y = a0 + a1*x)", "Точек"])
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.verticalHeader().setDefaultSectionSize(35)

        self.details_browser = QTextBrowser()
        self.details_browser.setPlaceholderText("Здесь будет детализация распределения точек...")

        self.res_splitter.addWidget(self.results_table)
        self.res_splitter.addWidget(self.details_browser)
        self.res_splitter.setSizes([200, 200])

        res_layout.addWidget(self.metrics_lbl)
        res_layout.addWidget(self.global_reg_lbl)
        res_layout.addWidget(self.res_splitter)

        left_panel.addWidget(data_group)
        left_panel.addWidget(params_group)
        left_panel.addWidget(action_group)
        left_panel.addWidget(res_group, 1)

        # --- ПРАВАЯ ПАНЕЛЬ (ГРАФИКИ) ---
        right_panel = QVBoxLayout()
        self.tabs = QTabWidget()
        self.view_cluster = QWebEngineView()
        self.view_error = QWebEngineView()
        self.tabs.addTab(self.view_cluster, "Кластерная модель")
        self.tabs.addTab(self.view_error, "Ошибки и отклонения")
        right_panel.addWidget(self.tabs)

        main_layout.addLayout(left_panel, 35)
        main_layout.addLayout(right_panel, 65)

    def toggle_theme(self):
        # Переключаем тему через qdarktheme
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.setStyleSheet(qdarktheme.load_stylesheet(self.current_theme))

        # Обновляем цвета в отчете под новую тему
        if self.last_results:
            self._render_details_html()

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть данные", "", "CSV (*.csv)")
        if path:
            self.csv_path = path
            self.file_info.setText(os.path.basename(path))

    def _rebuild_partial_inputs(self):
        while self.partial_form.count():
            child = self.partial_form.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.partial_inputs = []
        for i in range(self.r_input.value() - 1):
            edit = QLineEdit()
            edit.setPlaceholderText("Кол-во (или пусто)")
            self.partial_form.addRow(f"|P{i + 1}|:", edit)
            self.partial_inputs.append(edit)
        self._toggle_partial_panel()

    def _toggle_partial_panel(self, *_):
        self.partial_container.setVisible(self.mode_combo.checkedId() == 1)

    def run_model(self):
        if not self.csv_path:
            return QMessageBox.warning(self, "Внимание", "Сначала загрузите CSV файл.")
        try:
            x, y = load_csv(self.csv_path)
            r = self.r_input.value()
            sizes = self._build_sizes(len(x), r)

            self.solve_btn.setEnabled(False)
            self.solve_btn.setText("РАСЧЁТ В ПРОЦЕССЕ...")
            self.metrics_lbl.setText("⏳ Идет построение MILP модели...")
            self.global_reg_lbl.setText("")
            self.results_table.setRowCount(0)
            self.details_browser.clear()

            self.current_data = (x, y, r)
            self.worker = SolverThread(x, y, r, sizes)
            self.worker.finished.connect(self._on_success)
            self.worker.error.connect(self._on_error)
            self.worker.start()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _on_error(self, e_msg):
        self.solve_btn.setEnabled(True)
        self.solve_btn.setText(" ЗАПУСТИТЬ РАСЧЁТ")
        self.metrics_lbl.setText("❌ Ошибка при расчёте")
        QMessageBox.critical(self, "Ошибка", e_msg)

    def _on_success(self, results, g_coeffs):
        self.solve_btn.setEnabled(True)
        self.solve_btn.setText(" ЗАПУСТИТЬ РАСЧЁТ")

        self.last_results = results
        self.g_coeffs = g_coeffs
        x, y, r = self.current_data
        g0, g1 = g_coeffs

        # 1. Заполняем таблицу
        self.results_table.setRowCount(r)

        for i, (a0, a1) in enumerate(results["coeffs"]):
            cluster_points = results["clusters"].get(i, [])

            item_cluster = QTableWidgetItem(f"P{i + 1}")
            item_cluster.setTextAlignment(Qt.AlignCenter)
            self.results_table.setItem(i, 0, item_cluster)

            item_eq = QTableWidgetItem(f"{a0:.3f} + {a1:.3f}*x")
            self.results_table.setItem(i, 1, item_eq)

            item_pts = QTableWidgetItem(str(len(cluster_points)))
            item_pts.setTextAlignment(Qt.AlignCenter)
            self.results_table.setItem(i, 2, item_pts)

        # 2. Обновляем детализацию
        self._render_details_html()

        # 3. Обновляем метрики
        e_val = mean_percent_error(y, results["u"])
        self.metrics_lbl.setText(f"Средняя ошибка (E): {e_val:.4f}%")
        self.global_reg_lbl.setText(f"Общая регрессия: y = {g0:.4f} + {g1:.4f} * x")

        # 4. Отрисовка графиков
        c_fig = build_cluster_plot(results, x, y, g_coeffs)
        e_fig = build_error_plot(results, x, y)
        self._render_plots(c_fig, e_fig)
        self.pdf_btn.setEnabled(True)

    def _render_details_html(self):
        """Формирует HTML для детализации, подстраиваясь под выбранную тему"""
        results = self.last_results
        is_dark = self.current_theme == "dark"

        # Цвета из палитры qdarktheme
        text_color = "#e8eaed" if is_dark else "#202124"
        accent_color = "#8ab4f8" if is_dark else "#1a73e8"
        muted_color = "#9aa0a6" if is_dark else "#5f6368"
        border_color = "#3c4043" if is_dark else "#dadce0"

        html = f"<div style='font-family: sans-serif; font-size: 14px; color: {text_color}; line-height: 1.5;'>"
        html += f"<h3 style='color: {accent_color}; border-bottom: 1px solid {border_color}; padding-bottom: 5px; margin-top: 0;'>Детализация кластеров:</h3>"

        for i in range(len(results["coeffs"])):
            cluster_points = results["clusters"].get(i, [])
            readable_points = [str(idx + 1) for idx in cluster_points]
            points_str = ", ".join(readable_points)

            html += f"<p style='margin-bottom: 8px;'>"
            html += f"<b style='color: {accent_color};'>P{i + 1}:</b> "
            html += f"<span style='color: {muted_color}; font-family: monospace;'>[{points_str}]</span>"
            html += f"</p>"

        html += "</div>"
        self.details_browser.setHtml(html)

    def _render_plots(self, f1, f2):
        t = tempfile.gettempdir()
        p1 = os.path.join(t, "p1_cluster.html")
        p2 = os.path.join(t, "p2_error.html")
        config = {"scrollZoom": True, "displayModeBar": True}
        f1.write_html(p1, include_plotlyjs=True, config=config)
        f2.write_html(p2, include_plotlyjs=True, config=config)
        self.view_cluster.load(QUrl.fromLocalFile(p1))
        self.view_error.load(QUrl.fromLocalFile(p2))

    def _build_sizes(self, n, r):
        m = self.mode_combo.checkedId()
        if m == 0: return None
        if m == 2: b = n // r; s = [b] * r; s[-1] = n - b * (r - 1); return s
        s = [None] * r;
        f = 0
        for i, inp in enumerate(self.partial_inputs):
            v = int(inp.text() or 0);
            s[i] = v;
            f += v
        s[-1] = n - f
        return s

    def export_pdf(self):
        if self.last_results is None: return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт в PDF",
            f"cluster_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Files (*.pdf)"
        )

        if not file_path: return
        if not file_path.lower().endswith(".pdf"): file_path += ".pdf"

        try:
            with TemporaryDirectory() as tmp_dir:
                x, y, r = self.current_data
                g0, g1 = self.g_coeffs

                c_fig = build_cluster_plot(self.last_results, x, y, (g0, g1))
                e_fig = build_error_plot(self.last_results, x, y)

                p1 = f"{tmp_dir}/cluster_plot.png"
                p2 = f"{tmp_dir}/error_plot.png"

                c_fig.write_image(p1, width=1400, height=900, scale=2)
                e_fig.write_image(p2, width=1400, height=900, scale=2)

                with PdfPages(file_path) as pdf:
                    text_fig = Figure(figsize=(8.27, 11.69))
                    text_ax = text_fig.add_subplot(111)
                    text_ax.axis("off")

                    e_val = mean_percent_error(y, self.last_results["u"])
                    report_lines = [
                        "ОТЧЁТ ПО КЛАСТЕРНОЙ РЕГРЕССИИ",
                        f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                        "",
                        f"Средняя ошибка (E): {e_val:.4f}%",
                        f"Общая регрессия: y = {g0:.4f} + {g1:.4f} * x",
                        "",
                        "УРАВНЕНИЯ И РАСПРЕДЕЛЕНИЕ КЛАСТЕРОВ:"
                    ]

                    for i, (a0, a1) in enumerate(self.last_results["coeffs"]):
                        pts = self.last_results["clusters"].get(i, [])
                        readable_points = [str(idx + 1) for idx in pts]
                        points_str = ", ".join(readable_points)

                        report_lines.append(f"P{i + 1}: y = {a0:.4f} + {a1:.4f}*x")
                        report_lines.append(f"    Точек ({len(pts)}): [{points_str}]")

                    text_ax.text(0.02, 0.98, "\n".join(report_lines), va="top", ha="left", fontsize=10,
                                 family="monospace", wrap=True)
                    pdf.savefig(text_fig)

                    cluster_img = mpimg.imread(p1)
                    fig_cluster = Figure(figsize=(11.69, 8.27))
                    ax_cluster = fig_cluster.add_subplot(111)
                    ax_cluster.axis("off");
                    ax_cluster.imshow(cluster_img)
                    pdf.savefig(fig_cluster)

                    error_img = mpimg.imread(p2)
                    fig_error = Figure(figsize=(11.69, 8.27))
                    ax_error = fig_error.add_subplot(111)
                    ax_error.axis("off");
                    ax_error.imshow(error_img)
                    pdf.savefig(fig_error)

            QMessageBox.information(self, "PDF", f"Отчёт успешно сохранён:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "PDF", f"Ошибка сохранения PDF:\n{e}")