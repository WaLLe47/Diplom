"""Main application window — modern sidebar layout."""

import tempfile
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect, Qt, QUrl, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from analysis.metrics import mean_percent_error
from data.loader import load_csv
from gui.dialogs import DataPreviewDialog
from gui.loading_overlay import LoadingOverlay
from gui.pdf_export import export_report
from gui.sidebar import DRAWER_MARGIN, SIDEBAR_WIDTH, TOP_BAR_HEIGHT, Sidebar
from gui.styles import THEMES, build_stylesheet
from gui.worker import SolverThread
from visualization.plot_clusters import build_cluster_plot, build_error_plot


class _DrawerBackdrop(QWidget):
    """Dimmed layer behind the slide-out menu; click to dismiss."""

    clicked = Signal()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.clicked.emit()
        event.accept()


class _StatusDot(QLabel):
    """Small colored indicator for workflow state."""

    _COLORS = {
        "idle":    "#8b7aa8",
        "ready":   "#2dd4bf",
        "running": "#c084fc",
        "error":   "#fb7185",
        "success": "#2dd4bf",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(8, 8)
        self.set_state("idle")

    def set_state(self, state: str) -> None:
        color = self._COLORS.get(state, self._COLORS["idle"])
        self.setStyleSheet(
            f"background: {color}; border-radius: 4px; border: none;"
        )


class MainWindow(QWidget):
    """Top-level application window with persistent sidebar."""

    def __init__(self) -> None:
        super().__init__()
        self.csv_path: str | None = None
        self.loaded_data: tuple[list[float], list[float]] | None = None
        self.last_results: dict[str, Any] | None = None
        self.current_data: tuple[list[float], list[float], int] | None = None
        self.g_coeffs: tuple[float, float] | None = None
        self.worker: SolverThread | None = None
        self.current_theme: str = "dark"

        self.setObjectName("mainWindow")
        self.setWindowTitle("MILP Cluster Analysis")
        self.resize(1440, 900)
        self.setMinimumSize(960, 640)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(build_stylesheet(self.current_theme))
        self._build_ui()
        self._connect_signals()
        self._apply_theme_visuals()
        self._set_status("idle", "Ожидание запуска…")

    # ──────────────────────────────────── BUILD ───────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        accent = QWidget()
        accent.setObjectName("accentStrip")
        outer.addWidget(accent)

        self._top_bar = self._build_top_bar()
        outer.addWidget(self._top_bar)

        self._stack = QWidget()
        self._stack.setObjectName("mainStack")
        self._stack.setAttribute(Qt.WA_StyledBackground, True)
        stack_lay = QVBoxLayout(self._stack)
        stack_lay.setContentsMargins(0, 0, 0, 0)
        stack_lay.setSpacing(0)
        self._content = self._build_content()
        stack_lay.addWidget(self._content)
        outer.addWidget(self._stack, 1)

        self._drawer_backdrop = _DrawerBackdrop(self._stack)
        self._drawer_backdrop.setObjectName("drawerBackdrop")
        self._drawer_backdrop.setAttribute(Qt.WA_StyledBackground, True)
        self._drawer_backdrop.hide()

        self._sidebar = Sidebar(self._stack)
        self._sidebar.setFixedWidth(SIDEBAR_WIDTH)
        self._sidebar.hide()

        self._drawer_open = False
        self._drawer_anim = QPropertyAnimation(self._sidebar, b"geometry", self)
        self._drawer_anim.setDuration(220)
        self._drawer_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._overlay = LoadingOverlay(self)
        self._overlay.resize(self.size())
        self._overlay.hide()

    def _build_content(self) -> QWidget:
        area = QWidget()
        area.setObjectName("contentArea")
        area.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        inner = QWidget()
        inner.setObjectName("contentInner")
        inner.setAttribute(Qt.WA_StyledBackground, True)
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(18, 16, 18, 18)
        inner_lay.setSpacing(14)

        chart_panel = QWidget()
        chart_panel.setObjectName("chartPanel")
        chart_lay = QVBoxLayout(chart_panel)
        chart_lay.setContentsMargins(14, 10, 14, 14)
        chart_lay.setSpacing(8)

        self._tabs = QTabWidget()
        self._view_cluster = self._make_chart_view()
        self._view_error = self._make_chart_view()
        self._tabs.addTab(self._view_cluster, "Кластерная модель")
        self._tabs.addTab(self._view_error, "Ошибки и отклонения")
        chart_lay.addWidget(self._tabs)

        results_panel = QWidget()
        results_panel.setObjectName("resultsPanel")
        results_lay = QVBoxLayout(results_panel)
        results_lay.setContentsMargins(12, 10, 12, 12)
        results_lay.setSpacing(8)

        results_header = QHBoxLayout()
        results_header.setSpacing(8)
        results_title = QLabel("Результаты")
        results_title.setObjectName("panelTitle")
        self._cluster_count_lbl = QLabel("")
        self._cluster_count_lbl.setObjectName("panelCount")
        results_header.addWidget(results_title)
        results_header.addWidget(self._cluster_count_lbl)
        results_header.addStretch()
        results_lay.addLayout(results_header)

        result_row = QWidget()
        rr_lay = QHBoxLayout(result_row)
        rr_lay.setContentsMargins(0, 0, 0, 0)
        rr_lay.setSpacing(12)

        table_col = QVBoxLayout()
        table_col.setSpacing(6)
        tbl_title = QLabel("Уравнения кластеров")
        tbl_title.setObjectName("panelTitle")
        table_col.addWidget(tbl_title)
        self._table = self._make_table()
        table_col.addWidget(self._table)

        details_col = QVBoxLayout()
        details_col.setSpacing(6)
        det_title = QLabel("Распределение точек")
        det_title.setObjectName("panelTitle")
        details_col.addWidget(det_title)
        self._details = QTextBrowser()
        self._details.setPlaceholderText(
            "Детализация распределения точек по кластерам появится здесь…"
        )
        details_col.addWidget(self._details)

        rr_lay.addLayout(table_col, 3)
        rr_lay.addLayout(details_col, 2)
        results_lay.addWidget(result_row)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(chart_panel)
        splitter.addWidget(results_panel)
        splitter.setSizes([560, 240])
        splitter.setHandleWidth(8)
        inner_lay.addWidget(splitter, 1)

        layout.addWidget(inner, 1)
        return area

    def _build_top_bar(self) -> QWidget:
        top = QWidget()
        top.setObjectName("topBar")
        top.setFixedHeight(TOP_BAR_HEIGHT)
        top_lay = QHBoxLayout(top)
        top_lay.setContentsMargins(18, 0, 22, 0)
        top_lay.setSpacing(16)

        self._menu_btn = QPushButton("☰")
        self._menu_btn.setObjectName("menuOpenBtn")
        self._menu_btn.setToolTip("Открыть меню")
        self._menu_btn.setCursor(Qt.PointingHandCursor)
        top_lay.addWidget(self._menu_btn)

        page_title = QLabel("Анализ")
        page_title.setObjectName("topBarTitle")
        top_lay.addWidget(page_title)

        status_pill = QWidget()
        status_pill.setObjectName("statusPill")
        pill_lay = QHBoxLayout(status_pill)
        pill_lay.setContentsMargins(14, 6, 16, 6)
        pill_lay.setSpacing(8)

        self._status_dot = _StatusDot()
        self._metric_lbl = QLabel("Ожидание запуска…")
        self._metric_lbl.setObjectName("metricLabel")
        pill_lay.addWidget(self._status_dot)
        pill_lay.addWidget(self._metric_lbl)
        top_lay.addWidget(status_pill)

        top_lay.addStretch()

        reg_pill = QWidget()
        reg_pill.setObjectName("globalRegPill")
        reg_lay = QHBoxLayout(reg_pill)
        reg_lay.setContentsMargins(14, 6, 16, 6)
        self._global_reg_lbl = QLabel("Общая регрессия не рассчитана")
        self._global_reg_lbl.setObjectName("globalRegLabel")
        reg_lay.addWidget(self._global_reg_lbl)
        top_lay.addWidget(reg_pill)

        return top

    def _make_chart_view(self) -> QWidget:
        from PySide6.QtWebEngineWidgets import QWebEngineView

        wrap = QWidget()
        wrap.setObjectName("chartCanvas")
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        view = QWebEngineView()
        view.setStyleSheet("background: #ffffff;")
        lay.addWidget(view)
        wrap._web_view = view  # type: ignore[attr-defined]
        return wrap

    def _chart_web_view(self, tab_widget: QWidget):
        return tab_widget._web_view  # type: ignore[attr-defined]

    def _make_table(self) -> QTableWidget:
        t = QTableWidget(0, 3)
        t.setHorizontalHeaderLabels(["Кластер", "Уравнение", "Точек"])
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.verticalHeader().setVisible(False)
        t.setAlternatingRowColors(True)
        t.setShowGrid(False)
        return t

    # ──────────────────────────── SIGNALS ────────────────────────────────────

    def _connect_signals(self) -> None:
        sb = self._sidebar
        self._menu_btn.clicked.connect(self._open_drawer)
        sb.close_btn.clicked.connect(self._close_drawer)
        self._drawer_backdrop.clicked.connect(self._close_drawer)
        sb.load_btn.clicked.connect(self._load_file)
        sb.preview_btn.clicked.connect(self._show_preview)
        sb.solve_btn.clicked.connect(self._run_model)
        sb.pdf_btn.clicked.connect(self._export_pdf)
        sb.theme_changed.connect(self._apply_theme)

    # ──────────────────────────── SLOTS ──────────────────────────────────────

    def _drawer_rect(self, x: int) -> QRect:
        h = self._stack.height()
        return QRect(x, DRAWER_MARGIN, SIDEBAR_WIDTH, h - 2 * DRAWER_MARGIN)

    def _set_menu_btn_visible(self, visible: bool) -> None:
        self._menu_btn.setVisible(visible)

    def _open_drawer(self) -> None:
        if self._drawer_open:
            return
        self._drawer_open = True
        self._set_menu_btn_visible(False)
        h = self._stack.height()
        w = self._stack.width()
        self._sidebar.setFixedWidth(SIDEBAR_WIDTH)
        self._sidebar.show()
        self._drawer_backdrop.setGeometry(0, 0, w, h)
        self._drawer_backdrop.show()
        self._drawer_backdrop.raise_()
        self._sidebar.raise_()
        self._run_drawer_anim(
            self._drawer_rect(-SIDEBAR_WIDTH),
            self._drawer_rect(0),
        )

    def _close_drawer(self) -> None:
        if not self._drawer_open:
            return
        self._drawer_open = False
        self._set_menu_btn_visible(True)
        self._run_drawer_anim(
            self._drawer_rect(0),
            self._drawer_rect(-SIDEBAR_WIDTH),
            hide_after=True,
        )

    def _run_drawer_anim(
        self, start: QRect, end: QRect, *, hide_after: bool = False
    ) -> None:
        self._drawer_anim.stop()
        try:
            self._drawer_anim.finished.disconnect()
        except RuntimeError:
            pass
        self._drawer_anim.setStartValue(start)
        self._drawer_anim.setEndValue(end)
        if hide_after:
            self._drawer_anim.finished.connect(self._on_drawer_hidden)
        self._drawer_anim.start()

    def _on_drawer_hidden(self) -> None:
        self._sidebar.hide()
        self._drawer_backdrop.hide()
        self._set_menu_btn_visible(True)
        try:
            self._drawer_anim.finished.disconnect(self._on_drawer_hidden)
        except RuntimeError:
            pass

    def _sync_drawer_layout(self) -> None:
        if not hasattr(self, "_stack"):
            return
        w, h = self._stack.width(), self._stack.height()
        self._drawer_backdrop.setGeometry(0, 0, w, h)
        if self._drawer_anim.state() == QPropertyAnimation.Running:
            return
        x = 0 if self._drawer_open else -SIDEBAR_WIDTH
        if self._drawer_open or self._sidebar.isVisible():
            self._sidebar.setGeometry(self._drawer_rect(x))

    def _apply_theme(self, is_dark: bool) -> None:
        self.current_theme = "dark" if is_dark else "light"
        self.setStyleSheet(build_stylesheet(self.current_theme))
        self._apply_theme_visuals()
        if self.last_results:
            self._render_details()

    def _apply_theme_visuals(self) -> None:
        t = THEMES[self.current_theme]
        self._overlay.set_theme(self.current_theme)
        self._sidebar.theme_toggle.set_colors(t["accent_pink"], t["border"])

    def _set_status(self, state: str, text: str) -> None:
        self._status_dot.set_state(state)
        self._metric_lbl.setText(text)
        t = THEMES[self.current_theme]
        color_map = {
            "idle":    t["text_secondary"],
            "ready":   t["accent_green"],
            "running": t["accent"],
            "error":   t["accent_red"],
            "success": t["accent_green"],
        }
        self._metric_lbl.setStyleSheet(
            f"color: {color_map.get(state, t['text_secondary'])}; "
            f"font-weight: 600; background: transparent;"
        )

    def _load_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл данных", "", "CSV (*.csv)"
        )
        if not path:
            return
        try:
            x, y = load_csv(path)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка загрузки", str(exc))
            return

        self.csv_path = path
        self.loaded_data = (x, y)
        self.current_data = None
        self.last_results = None
        self.g_coeffs = None

        self._sidebar.set_file_loaded(Path(path).name, len(x))
        self._sidebar.pdf_btn.setEnabled(False)
        self._set_status("ready", "Данные загружены — готово к расчёту")
        self._global_reg_lbl.setText("Общая регрессия не рассчитана")
        self._cluster_count_lbl.setText("")
        self._table.setRowCount(0)
        self._details.clear()
        self._show_preview()

    def _show_preview(self) -> None:
        if not self.csv_path or not self.loaded_data:
            QMessageBox.warning(self, "Внимание", "Сначала загрузите CSV файл.")
            return
        x, y = self.loaded_data
        DataPreviewDialog(self.csv_path, x, y, self).exec()

    def _run_model(self) -> None:
        if not self.loaded_data:
            QMessageBox.warning(self, "Внимание", "Сначала загрузите CSV файл.")
            return
        try:
            x, y = self.loaded_data
            r = self._sidebar.r_spin.value()
            sizes = self._sidebar.get_cluster_sizes(len(x), r)
            self._set_solving(True)
            self.current_data = (x, y, r)
            self.worker = SolverThread(x, y, r, sizes)
            self.worker.finished.connect(self._on_success)
            self.worker.error.connect(self._on_error)
            self.worker.start()
        except Exception as exc:
            self._set_solving(False)
            QMessageBox.critical(self, "Ошибка", str(exc))

    def _set_solving(self, active: bool) -> None:
        self._sidebar.set_solving(active)
        if active:
            self._set_status("running", "Построение MILP модели…")
            self._global_reg_lbl.setText("Расчёт в процессе…")
            self._cluster_count_lbl.setText("")
            self._table.setRowCount(0)
            self._details.clear()
            self._overlay.show_loading()
        else:
            self._overlay.hide_loading()

    def _on_error(self, msg: str) -> None:
        self._set_solving(False)
        self._set_status("error", "Ошибка при расчёте")
        QMessageBox.critical(self, "Ошибка решателя", msg)

    def _on_success(
        self, results: dict[str, Any], g_coeffs: tuple[float, float]
    ) -> None:
        self._set_solving(False)
        self.last_results = results
        self.g_coeffs = g_coeffs

        if not self.current_data:
            return

        x, y, r = self.current_data
        self._fill_table(results, r)
        self._render_details()
        self._render_metrics(y, results, g_coeffs)
        self._render_plots(
            build_cluster_plot(results, x, y, g_coeffs),
            build_error_plot(results, x, y),
        )
        self._sidebar.pdf_btn.setEnabled(True)
        self._cluster_count_lbl.setText(f"{r} кластеров")

    # ──────────────────────────── RENDER ─────────────────────────────────────

    def _fill_table(self, results: dict[str, Any], r: int) -> None:
        self._table.setRowCount(r)
        for idx, (a0, a1) in enumerate(results["coeffs"]):
            pts = results["clusters"].get(idx, [])

            c = QTableWidgetItem(f"P{idx + 1}")
            c.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(idx, 0, c)

            self._table.setItem(idx, 1, QTableWidgetItem(f"{a0:.4f} + {a1:.4f}·x"))

            n = QTableWidgetItem(str(len(pts)))
            n.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(idx, 2, n)

    def _render_metrics(
        self,
        y: list[float],
        results: dict[str, Any],
        g_coeffs: tuple[float, float],
    ) -> None:
        g0, g1 = g_coeffs
        err = mean_percent_error(y, results["u"])
        self._set_status("success", f"Средняя ошибка (E): {err:.4f}%")
        self._global_reg_lbl.setText(f"y = {g0:.4f} + {g1:.4f}·x")

    def _render_details(self) -> None:
        if not self.last_results:
            return
        t = THEMES[self.current_theme]
        rows = []
        for idx in range(len(self.last_results["coeffs"])):
            pts = [str(p + 1) for p in self.last_results["clusters"].get(idx, [])]
            a0, a1 = self.last_results["coeffs"][idx]
            rows.append(
                f"<div style='margin:0 0 10px 0;padding:10px 12px;"
                f"background:{t['bg_elevated']};border:1px solid {t['border']};"
                f"border-radius:12px;border-left:3px solid {t['accent_pink']};'>"
                f"<div style='margin-bottom:4px;'>"
                f"<b style='color:{t['accent_pink']};font-size:13px;'>P{idx + 1}</b>"
                f"<span style='color:{t['text_muted']};font-size:11px;"
                f"margin-left:8px;'>{len(pts)} точек</span></div>"
                f"<div style='color:{t['text_secondary']};font-size:12px;"
                f"font-family:Consolas,monospace;margin-bottom:4px;'>"
                f"y = {a0:.4f} + {a1:.4f}·x</div>"
                f"<div style='color:{t['text_muted']};font-size:11px;"
                f"line-height:1.4;'>[{escape(', '.join(pts))}]</div></div>"
            )
        html = (
            f"<div style='font-family:\"Segoe UI\",sans-serif;"
            f"color:{t['text_primary']};'>"
            + "".join(rows)
            + "</div>"
        )
        self._details.setHtml(html)

    def _render_plots(self, cluster_fig, error_fig) -> None:
        tmp = Path(tempfile.gettempdir())
        c_path = tmp / "milp_cluster.html"
        e_path = tmp / "milp_error.html"
        cfg = {"scrollZoom": True, "displayModeBar": True}
        cluster_fig.write_html(c_path, include_plotlyjs=True, config=cfg)
        error_fig.write_html(e_path, include_plotlyjs=True, config=cfg)
        self._chart_web_view(self._view_cluster).load(QUrl.fromLocalFile(str(c_path)))
        self._chart_web_view(self._view_error).load(QUrl.fromLocalFile(str(e_path)))

    # ──────────────────────────── PDF ────────────────────────────────────────

    def _export_pdf(self) -> None:
        if not self.last_results or not self.current_data or not self.g_coeffs:
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт", f"milp_report_{ts}.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return
        out = Path(path)
        if out.suffix.lower() != ".pdf":
            out = out.with_suffix(".pdf")
        try:
            file_name = Path(self.csv_path).name if self.csv_path else "unknown"
            export_report(out, self.last_results, self.current_data, self.g_coeffs, file_name)
            QMessageBox.information(self, "Готово", f"Отчёт сохранён:\n{out}")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка PDF", str(exc))

    # ──────────────────────────── EVENTS ─────────────────────────────────────

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._sync_drawer_layout()
        if hasattr(self, "_overlay"):
            self._overlay.resize(self.size())
            self._overlay.raise_()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if not getattr(self, "_drawer_initialized", False):
            self._drawer_initialized = True
            self._open_drawer()
