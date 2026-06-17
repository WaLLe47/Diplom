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
from data.loader import load_excel
import pandas as pd
from gui.database import get_db
from gui.dialogs import DataPreviewDialog
from gui.history_dialog import HistoryDialog
from gui.loading_overlay import LoadingOverlay
from gui.pdf_export import export_report
from gui.sidebar import DRAWER_MARGIN, SIDEBAR_WIDTH, TOP_BAR_HEIGHT, Sidebar
from gui.styles import FONT_MONO, FONT_SANS
# styles applied globally via qt-material in app.py
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
        self.loaded_df: pd.DataFrame | None = None          # full DataFrame
        self.sel_x_cols: list[str] = []                     # chosen X columns
        self.sel_y_col: str = ""                            # chosen Y column
        self.last_results: dict[str, Any] | None = None
        self.current_data: tuple | None = None              # (X, y, r, x_cols, y_col)
        self.g_coeffs: tuple[float, float] | None = None
        self.worker: SolverThread | None = None
        self.current_dataset_id: int | None = None          # row id in local DB
        self.current_result_id: int | None = None
        self._history_win: HistoryDialog | None = None

        self.setObjectName("mainWindow")
        self.setWindowTitle("MILP Cluster Analysis")
        self.resize(1440, 900)
        self.setMinimumSize(960, 640)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._build_ui()
        self._connect_signals()
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
        inner_lay.setContentsMargins(0, 0, 0, 0)
        inner_lay.setSpacing(0)

        chart_panel = QWidget()
        chart_panel.setObjectName("chartPanel")
        chart_panel.setMinimumHeight(0)
        chart_lay = QVBoxLayout(chart_panel)
        chart_lay.setContentsMargins(0, 0, 0, 0)
        chart_lay.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("chartTabs")
        self._view_cluster = self._make_chart_view()
        self._view_error = self._make_chart_view()
        self._tabs.addTab(self._view_cluster, "Кластерная модель")
        self._tabs.addTab(self._view_error, "Ошибки и отклонения")
        chart_lay.addWidget(self._tabs)

        results_panel = QWidget()
        results_panel.setObjectName("resultsPanel")
        results_panel.setMinimumHeight(200)
        results_lay = QVBoxLayout(results_panel)
        results_lay.setContentsMargins(0, 0, 0, 0)
        results_lay.setSpacing(8)

        # ── Header row ──────────────────────────────────────────────────────
        results_header = QHBoxLayout()
        results_header.setContentsMargins(16, 10, 16, 0)
        results_header.setSpacing(8)
        results_title = QLabel("Результаты")
        results_title.setObjectName("panelTitle")
        self._cluster_count_lbl = QLabel("")
        self._cluster_count_lbl.setObjectName("panelCount")
        results_header.addWidget(results_title)
        results_header.addWidget(self._cluster_count_lbl)
        results_header.addStretch()
        results_lay.addLayout(results_header)

        # ── Two-column horizontal splitter ───────────────────────────────────
        h_split = QSplitter(Qt.Horizontal)
        h_split.setHandleWidth(8)
        h_split.setChildrenCollapsible(False)

        # Left: equations table
        table_wrap = QWidget()
        tw_lay = QVBoxLayout(table_wrap)
        tw_lay.setContentsMargins(0, 0, 0, 0)
        tw_lay.setSpacing(6)
        tbl_title = QLabel("Уравнения кластеров")
        tbl_title.setObjectName("panelTitle")
        tw_lay.addWidget(tbl_title)
        self._table = self._make_table()
        tw_lay.addWidget(self._table, 1)

        # Right: point distribution
        details_wrap = QWidget()
        dw_lay = QVBoxLayout(details_wrap)
        dw_lay.setContentsMargins(0, 0, 0, 0)
        dw_lay.setSpacing(6)
        det_title = QLabel("Распределение точек")
        det_title.setObjectName("panelTitle")
        dw_lay.addWidget(det_title)
        self._details = QTextBrowser()
        self._details.setPlaceholderText(
            "Детализация распределения точек по кластерам появится здесь…"
        )
        self._details.setTextInteractionFlags(Qt.NoTextInteraction)
        self._details.setOpenLinks(False)
        self._details.setMinimumWidth(220)
        dw_lay.addWidget(self._details, 1)

        h_split.addWidget(table_wrap)
        h_split.addWidget(details_wrap)
        h_split.setSizes([600, 300])

        h_split.setContentsMargins(8, 0, 8, 8)
        results_lay.addWidget(h_split, 1)

        # ── Main vertical splitter ───────────────────────────────────────────
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(chart_panel)
        splitter.addWidget(results_panel)
        splitter.setSizes([520, 260])
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setHandleWidth(10)
        splitter.setChildrenCollapsible(False)
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
        from PySide6.QtWidgets import QSizePolicy

        wrap = QWidget()
        wrap.setObjectName("chartCanvas")
        wrap.setMinimumHeight(0)
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        view = QWebEngineView()
        view.setMinimumSize(0, 0)
        view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        view.setHtml(
            "<html><body style='background:#1a1625;margin:0'></body></html>"
        )
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
        sb.history_btn.clicked.connect(self._open_history)

    # ──────────────────────────── SLOTS ──────────────────────────────────────

    def _drawer_rect(self, x: int) -> QRect:
        return QRect(x, 0, SIDEBAR_WIDTH, self._stack.height())

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

    def _set_status(self, state: str, text: str) -> None:
        self._status_dot.set_state(state)
        self._metric_lbl.setText(text)
        color_map = {
            "idle":    "rgba(255,255,255,0.50)",
            "ready":   "#26c6da",
            "running": "#ab47bc",
            "error":   "#f44336",
            "success": "#26c6da",
        }
        self._metric_lbl.setStyleSheet(
            f"color: {color_map.get(state, 'rgba(255,255,255,0.50)')}; "
            f"font-weight: 600; background: transparent;"
        )

    def _load_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл Excel", "",
            "Excel файлы (*.xlsx *.xls *.xlsm *.xlsb *.ods);;Все файлы (*.*)"
        )
        if not path:
            return
        try:
            df = load_excel(path)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка загрузки", str(exc))
            return

        self.csv_path = path
        self.loaded_df = df
        # Default: last col = Y, rest = X
        self.sel_y_col = df.columns[-1]
        self.sel_x_cols = list(df.columns[:-1])
        self.current_data = None
        self.last_results = None
        self.g_coeffs = None
        self.current_result_id = None

        # Persist the imported dataset in the local store.
        try:
            self.current_dataset_id = get_db().save_dataset(Path(path).name, df)
        except Exception:  # noqa: BLE001 — storage must never block the workflow
            self.current_dataset_id = None

        self._sidebar.set_file_loaded(Path(path).name, len(df))
        self._sidebar.pdf_btn.setEnabled(False)
        self._set_status("ready", "Данные загружены — готово к расчёту")
        self._global_reg_lbl.setText("Общая регрессия не рассчитана")
        self._cluster_count_lbl.setText("")
        self._table.setRowCount(0)
        self._details.clear()
        self._show_preview()

    def _show_preview(self) -> None:
        if not self.csv_path or self.loaded_df is None:
            QMessageBox.warning(self, "Внимание", "Сначала загрузите файл Excel.")
            return
        dlg = DataPreviewDialog(
            self.csv_path, self.loaded_df,
            self.sel_x_cols, self.sel_y_col, self
        )
        if dlg.exec():
            self.sel_x_cols = dlg.selected_x_cols
            self.sel_y_col = dlg.selected_y_col
            n_x = len(self.sel_x_cols)
            self._set_status(
                "ready",
                f"X: {n_x} переменных · Y: {self.sel_y_col}"
            )

    def _run_model(self) -> None:
        if self.loaded_df is None:
            QMessageBox.warning(self, "Внимание", "Сначала загрузите файл Excel.")
            return
        if not self.sel_x_cols or not self.sel_y_col:
            QMessageBox.warning(self, "Внимание", "Выберите столбцы X и Y в предпросмотре.")
            return
        try:
            X = self.loaded_df[self.sel_x_cols].values.tolist()
            y = self.loaded_df[self.sel_y_col].tolist()
            r = self._sidebar.r_spin.value()
            sizes = self._sidebar.get_cluster_sizes(len(X), r)
            self._set_solving(True)
            self.current_data = (X, y, r, self.sel_x_cols, self.sel_y_col)
            self.worker = SolverThread(X, y, r, sizes, self.sel_x_cols, self.sel_y_col)
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

        X, y, r, x_cols, y_col = self.current_data
        self._fill_table(results, r, x_cols)
        self._render_details(x_cols)
        self._render_metrics(y, results, g_coeffs)
        # For 2-D plot use first X column only; with multiple X show first
        x0 = [row[0] for row in X]
        self._render_plots(
            build_cluster_plot(results, x0, y, g_coeffs),
            build_error_plot(results, x0, y),
        )
        self._sidebar.pdf_btn.setEnabled(True)
        self._cluster_count_lbl.setText(f"{r} кластеров")

        # Persist the computed result in the local store.
        try:
            self.current_result_id = get_db().save_result(
                self.current_dataset_id, r, list(x_cols), y_col,
                mean_percent_error(y, results["u"]), g_coeffs,
                results["coeffs"], results["clusters"],
            )
        except Exception:  # noqa: BLE001 — storage must never block the workflow
            self.current_result_id = None

    # ──────────────────────────── RENDER ─────────────────────────────────────

    def _fill_table(self, results: dict[str, Any], r: int, x_cols: list[str] | None = None) -> None:
        self._table.setRowCount(r)
        for idx, (a0, a1_list) in enumerate(results["coeffs"]):
            pts = results["clusters"].get(idx, [])

            c = QTableWidgetItem(f"P{idx + 1}")
            c.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(idx, 0, c)

            terms = [f"{a0:.4f}"]
            for fi, a in enumerate(a1_list):
                col_name = x_cols[fi] if x_cols and fi < len(x_cols) else f"x{fi}"
                terms.append(f"{a:+.4f}·{col_name}")
            self._table.setItem(idx, 1, QTableWidgetItem(" ".join(terms)))

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

    def _render_details(self, x_cols: list[str] | None = None) -> None:
        if not self.last_results:
            return
        cols = x_cols or self.sel_x_cols
        rows = []
        for idx in range(len(self.last_results["coeffs"])):
            pts = [str(p + 1) for p in self.last_results["clusters"].get(idx, [])]
            a0, a1_list = self.last_results["coeffs"][idx]
            terms = [f"{a0:.4f}"]
            for fi, a in enumerate(a1_list):
                cn = cols[fi] if cols and fi < len(cols) else f"x{fi}"
                terms.append(f"{a:+.4f}·{cn}")
            eq = "y = " + " ".join(terms)
            rows.append(
                f"<div style='margin:0 0 10px 0;padding:10px 12px;"
                f"background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.10);"
                f"border-radius:6px;border-left:3px solid #e040fb;'>"
                f"<div style='margin-bottom:4px;'>"
                f"<b style='color:#e040fb;font-size:13px;'>P{idx + 1}</b>"
                f"<span style='color:rgba(255,255,255,0.45);font-size:12px;"
                f"margin-left:8px;'>{len(pts)} точек</span></div>"
                f"<div style='color:rgba(255,255,255,0.85);font-size:12px;"
                f"font-family:{FONT_MONO};margin-bottom:4px;'>{escape(eq)}</div>"
                f"<div style='color:rgba(255,255,255,0.45);font-size:12px;"
                f"line-height:1.4;'>[{escape(', '.join(pts))}]</div></div>"
            )
        html = (
            f"<div style='font-family:{FONT_SANS};color:#ffffff;'>"
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
            X, y, r, x_cols, y_col = self.current_data
            export_report(
                out, self.last_results, (X, y, r, x_cols), self.g_coeffs,
                file_name, y_name=y_col or "y",
            )
            # Keep a copy of the report inside the local store.
            try:
                get_db().save_report(self.current_result_id, out.name, out.read_bytes())
            except Exception:  # noqa: BLE001 — storage must never block the export
                pass
            QMessageBox.information(self, "Готово", f"Отчёт сохранён:\n{out}")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка PDF", str(exc))

    # ──────────────────────────── HISTORY ────────────────────────────────────

    def _open_history(self) -> None:
        if self._history_win is None:
            self._history_win = HistoryDialog(self)
            self._history_win.dataset_chosen.connect(self._load_dataset_from_db)
        self._history_win.refresh()
        self._history_win.show()
        self._history_win.raise_()
        self._history_win.activateWindow()

    def _load_dataset_from_db(self, dataset_id: int) -> None:
        """Reload a stored dataset back into the workflow."""
        try:
            df = get_db().get_dataset_df(dataset_id)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить набор:\n{exc}")
            return
        self.csv_path = f"dataset_{dataset_id}"
        self.loaded_df = df
        self.sel_y_col = df.columns[-1]
        self.sel_x_cols = list(df.columns[:-1])
        self.current_data = None
        self.last_results = None
        self.g_coeffs = None
        self.current_dataset_id = dataset_id
        self.current_result_id = None
        self._sidebar.set_file_loaded(f"Из хранилища #{dataset_id}", len(df))
        self._sidebar.pdf_btn.setEnabled(False)
        self._set_status("ready", "Набор загружен из хранилища — готово к расчёту")
        self._global_reg_lbl.setText("Общая регрессия не рассчитана")
        self._cluster_count_lbl.setText("")
        self._table.setRowCount(0)
        self._details.clear()
        if self._history_win is not None:
            self._history_win.close()

    # ──────────────────────────── EVENTS ─────────────────────────────────────

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._sync_drawer_layout()
        if hasattr(self, "_overlay"):
            self._overlay.resize(self.size())
            self._overlay.raise_()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._sync_drawer_layout()