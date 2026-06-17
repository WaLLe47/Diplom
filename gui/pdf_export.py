"""PDF report generation — presentable, branded multi-page report."""

import textwrap
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import matplotlib
import numpy as np
from matplotlib import image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch

from analysis.metrics import mean_percent_error
from visualization.plot_clusters import build_cluster_plot, build_error_plot

# ── Shared visual identity (matches the application theme) ──────────────────────
_ACCENT = ["#f97316", "#e040fb", "#ab47bc", "#26c6da"]   # orange → pink → purple → cyan
_GRAD = LinearSegmentedColormap.from_list("milp_accent", _ACCENT)

_INK = "#2e1065"          # deep purple — headings
_INK_SOFT = "#5b21b6"     # softer purple — body
_MUTED = "#8b7aa8"        # muted labels
_CARD_BG = "#f7f5fc"      # light card fill
_CARD_BORDER = "#e6d8f7"  # card outline
_PINK = "#c026d3"
_CYAN = "#0891b2"

# Harmonise PDF typography with the rest of the project.
matplotlib.rcParams["font.family"] = "sans-serif"
matplotlib.rcParams["font.sans-serif"] = [
    "Segoe UI", "Segoe UI Variable", "DejaVu Sans", "Arial",
]
matplotlib.rcParams["font.monospace"] = [
    "Cascadia Mono", "Consolas", "Courier New", "DejaVu Sans Mono",
]
matplotlib.rcParams["axes.unicode_minus"] = False

_A4_PORTRAIT = (8.27, 11.69)
_A4_LANDSCAPE = (11.69, 8.27)


# ── public API ──────────────────────────────────────────────────────────────────

def export_report(
    output_path: Path,
    results: dict[str, Any],
    current_data: tuple[list[list[float]], list[float], int, list[str] | None],
    g_coeffs: tuple[float, float],
    file_name: str,
    y_name: str = "y",
) -> None:
    """Build a compact PDF report: one overview page + two chart pages."""
    X, y, _r, x_cols = current_data
    x0 = [row[0] for row in X]

    with TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        cluster_png = tmp / "cluster_plot.png"
        error_png = tmp / "error_plot.png"

        build_cluster_plot(results, x0, y, g_coeffs).write_image(
            cluster_png, width=1400, height=900, scale=2
        )
        build_error_plot(results, x0, y).write_image(
            error_png, width=1400, height=900, scale=2
        )

        with PdfPages(output_path) as pdf:
            _write_overview_page(pdf, results, y, x_cols, g_coeffs, file_name, y_name)
            _write_chart_page(pdf, cluster_png, "Кластерная линейная регрессия", "Стр. 2")
            _write_chart_page(pdf, error_png, "Фактические и расчётные значения", "Стр. 3")


# ── helpers ───────────────────────────────────────────────────────────────────

def _format_equation(
    a0: float,
    a1_list: list[float],
    x_cols: list[str] | None = None,
    y_name: str = "y",
) -> str:
    terms = [f"{a0:.4f}"]
    for fi, a in enumerate(a1_list):
        col_name = x_cols[fi] if x_cols and fi < len(x_cols) else f"x{fi}"
        terms.append(f"{a:+.4f}·{col_name}")
    return f"{y_name} = " + " ".join(terms)


def _new_axes(fig: Figure):
    """Full-figure transparent axes with a 0..1 coordinate system."""
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.patch.set_alpha(0)
    return ax


def _gradient_band(fig: Figure, y0: float, height: float) -> None:
    band = fig.add_axes([0, y0, 1, height])
    band.axis("off")
    grad = np.linspace(0, 1, 512).reshape(1, -1)
    band.imshow(grad, aspect="auto", cmap=_GRAD, extent=[0, 1, 0, 1], origin="lower")


def _card(ax, x, y, w, h, *, fc=_CARD_BG, ec=_CARD_BORDER, lw=1.0) -> None:
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0,rounding_size=0.012",
        mutation_aspect=_A4_PORTRAIT[1] / _A4_PORTRAIT[0],
        facecolor=fc, edgecolor=ec, linewidth=lw,
        transform=ax.transAxes, clip_on=False,
    )
    ax.add_patch(patch)


def _footer(ax, page_label: str) -> None:
    ax.plot([0.06, 0.94], [0.045, 0.045], color=_CARD_BORDER, lw=1.0,
            transform=ax.transAxes, clip_on=False)
    ax.text(0.06, 0.028, "MILP Cluster Analysis · кластерная регрессия (HiGHS)",
            transform=ax.transAxes, fontsize=8, color=_MUTED, va="center")
    ax.text(0.94, 0.028, page_label, transform=ax.transAxes,
            fontsize=8, color=_MUTED, va="center", ha="right")


# ── pages ────────────────────────────────────────────────────────────────────

def _write_overview_page(
    pdf: PdfPages,
    results: dict[str, Any],
    y: list[float],
    x_cols: list[str] | None,
    g_coeffs: tuple[float, float],
    file_name: str,
    y_name: str,
) -> None:
    """Single overview page: parameters, metrics and cluster equations."""
    g0, g1 = g_coeffs
    error_value = mean_percent_error(y, results["u"])
    x_name = x_cols[0] if x_cols else "x"
    coeffs = results["coeffs"]
    clusters = results["clusters"]
    n_clusters = len(coeffs)

    fig = Figure(figsize=_A4_PORTRAIT)
    fig.patch.set_facecolor("white")

    _gradient_band(fig, 0.918, 0.082)
    ax = _new_axes(fig)

    # Title sits on the gradient band.
    ax.text(0.06, 0.963, "Отчёт по кластерной регрессии",
            color="white", fontsize=20, fontweight="bold", va="center")
    ax.text(0.06, 0.936, "Mixed-Integer Linear Programming · решатель HiGHS",
            color="white", fontsize=11, va="center", alpha=0.95)

    # ── Parameters (compact 2×2 grid) ───────────────────────────────────────
    ax.text(0.06, 0.888, "ПАРАМЕТРЫ", fontsize=11, fontweight="bold",
            color=_MUTED, va="center")
    _card(ax, 0.06, 0.792, 0.88, 0.082)
    # (label_x, value_x, y) for each cell — left column then right column.
    meta = [
        ("Дата", datetime.now().strftime("%d.%m.%Y  %H:%M"), 0.085, 0.215, 0.852),
        ("Наблюдений", str(len(y)), 0.085, 0.215, 0.812),
        ("Исходный файл", file_name, 0.535, 0.690, 0.852),
        ("Кластеров", str(n_clusters), 0.535, 0.690, 0.812),
    ]
    for label, value, lx, vx, ly in meta:
        ax.text(lx, ly, label, fontsize=11, color=_MUTED, va="center")
        ax.text(vx, ly, value, fontsize=11, color=_INK_SOFT,
                fontweight="bold", va="center")

    # ── Quality metrics ─────────────────────────────────────────────────────
    ax.text(0.06, 0.760, "ПОКАЗАТЕЛИ КАЧЕСТВА", fontsize=11, fontweight="bold",
            color=_MUTED, va="center")

    _card(ax, 0.06, 0.648, 0.42, 0.094, fc="#fdf2fb", ec="#f3d4ef")
    ax.text(0.085, 0.716, "Средняя ошибка (E)", fontsize=11, color=_MUTED, va="center")
    ax.text(0.085, 0.676, f"{error_value:.4f} %", fontsize=22, fontweight="bold",
            color=_PINK, va="center")

    _card(ax, 0.52, 0.648, 0.42, 0.094, fc="#ecfeff", ec="#cfeef3")
    ax.text(0.545, 0.716, "Кластеров построено", fontsize=11, color=_MUTED, va="center")
    ax.text(0.545, 0.676, str(n_clusters), fontsize=22, fontweight="bold",
            color=_CYAN, va="center")

    _card(ax, 0.06, 0.560, 0.88, 0.070, fc=_CARD_BG, ec=_CARD_BORDER)
    ax.text(0.085, 0.609, "Общая (единая) регрессия", fontsize=11,
            color=_MUTED, va="center")
    ax.text(0.085, 0.580, f"{y_name} = {g0:.4f} {g1:+.4f}·{x_name}",
            fontsize=13, color=_INK, fontfamily="monospace", va="center")

    # ── Cluster equations table ─────────────────────────────────────────────
    ax.text(0.06, 0.524, "УРАВНЕНИЯ КЛАСТЕРОВ", fontsize=11, fontweight="bold",
            color=_MUTED, va="center")

    eq_fs = 8.5 if n_clusters <= 14 else 7.0
    wrap_w = 66 if eq_fs >= 8.5 else 80  # chars that fit the equation column
    # Wrap long (multi-feature) equations so they never overrun the next column.
    wrapped_eqs = [
        textwrap.fill(
            _format_equation(a0, a1_list, x_cols, y_name),
            width=wrap_w, subsequent_indent="      ",
        )
        for a0, a1_list in coeffs
    ]
    max_lines = max((eq.count("\n") + 1 for eq in wrapped_eqs), default=1)
    col_text = [
        [f"P{idx + 1}", wrapped_eqs[idx], str(len(clusters.get(idx, [])))]
        for idx in range(n_clusters)
    ]

    table_top = 0.508
    line_h = 0.0145 * (eq_fs / 8.5)
    row_h = min(0.05, line_h * max_lines + 0.014)
    table_h = row_h * (n_clusters + 1)
    tbl = ax.table(
        cellText=col_text,
        colLabels=["Кластер", "Уравнение регрессии", "Точек"],
        colWidths=[0.13, 0.72, 0.15],
        cellLoc="left",
        bbox=[0.06, table_top - table_h, 0.88, table_h],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(eq_fs)

    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor("#ffffff")
        cell.set_linewidth(1.2)
        cell.PAD = 0.03
        if row == 0:  # header
            cell.set_facecolor(_INK)
            cell.set_text_props(color="white", fontweight="bold", fontsize=9)
            cell._loc = "center"
        else:
            cell.set_facecolor("#faf8fe" if row % 2 else _CARD_BG)
            cell.set_text_props(color=_INK_SOFT)
            if col == 1:
                cell.set_text_props(color=_INK, fontfamily="monospace", fontsize=eq_fs)
            else:
                cell._loc = "center"

    # ── Cluster composition ─────────────────────────────────────────────────
    comp_title_y = table_top - table_h - 0.040
    ax.text(0.06, comp_title_y, "СОСТАВ КЛАСТЕРОВ (номера точек)", fontsize=11,
            fontweight="bold", color=_MUTED, va="center")

    blocks = []
    for idx in range(n_clusters):
        pts = clusters.get(idx, [])
        nums = ", ".join(str(p + 1) for p in pts)
        body = textwrap.fill(nums, width=95, subsequent_indent="        ")
        blocks.append(f"P{idx + 1} ({len(pts)}):  {body}")
    comp_text = "\n".join(blocks)

    ax.text(0.06, comp_title_y - 0.022, comp_text, fontsize=8.5, color=_INK_SOFT,
            va="top", fontfamily="monospace", linespacing=1.55)

    _footer(ax, "Стр. 1")
    pdf.savefig(fig)


def _write_chart_page(
    pdf: PdfPages, image_path: Path, title: str, page_label: str = ""
) -> None:
    img = mpimg.imread(image_path)
    fig = Figure(figsize=_A4_LANDSCAPE)
    fig.patch.set_facecolor("white")

    _gradient_band(fig, 0.93, 0.07)
    ax = _new_axes(fig)
    ax.text(0.05, 0.962, title, color="white", fontsize=16,
            fontweight="bold", va="center")

    img_ax = fig.add_axes([0.04, 0.06, 0.92, 0.84])
    img_ax.axis("off")
    img_ax.imshow(img)

    _footer(ax, page_label)
    pdf.savefig(fig)
