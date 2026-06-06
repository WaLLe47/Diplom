"""PDF report generation."""

import tempfile
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from matplotlib import image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from analysis.metrics import mean_percent_error
from visualization.plot_clusters import build_cluster_plot, build_error_plot


def export_report(
    output_path: Path,
    results: dict[str, Any],
    current_data: tuple[list[float], list[float], int],
    g_coeffs: tuple[float, float],
    file_name: str,
) -> None:
    """Build a multi-page PDF report with summary + two charts."""
    x, y, _r = current_data

    with TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        cluster_png = tmp / "cluster_plot.png"
        error_png = tmp / "error_plot.png"

        build_cluster_plot(results, x, y, g_coeffs).write_image(
            cluster_png, width=1400, height=900, scale=2
        )
        build_error_plot(results, x, y).write_image(
            error_png, width=1400, height=900, scale=2
        )

        with PdfPages(output_path) as pdf:
            _write_summary_page(pdf, results, current_data, g_coeffs, file_name)
            _write_image_page(pdf, cluster_png)
            _write_image_page(pdf, error_png)


def _write_summary_page(
    pdf: PdfPages,
    results: dict[str, Any],
    current_data: tuple[list[float], list[float], int],
    g_coeffs: tuple[float, float],
    file_name: str,
) -> None:
    _x, y, _r = current_data
    g0, g1 = g_coeffs
    error_value = mean_percent_error(y, results["u"])

    lines = [
        "═══════════════════════════════════════",
        "  ОТЧЁТ ПО КЛАСТЕРНОЙ РЕГРЕССИИ (MILP)",
        "═══════════════════════════════════════",
        "",
        f"  Дата:           {datetime.now().strftime('%d.%m.%Y  %H:%M:%S')}",
        f"  Исходный файл:  {file_name}",
        f"  Наблюдений:     {len(y)}",
        f"  Кластеров:      {len(results['coeffs'])}",
        "",
        "─── Показатели качества ───────────────",
        f"  Средняя ошибка (E): {error_value:.4f} %",
        f"  Общая регрессия:    y = {g0:.4f} + {g1:.4f}·x",
        "",
        "─── Уравнения кластеров ───────────────",
    ]

    for idx, (a0, a1) in enumerate(results["coeffs"]):
        pts = results["clusters"].get(idx, [])
        nums = ", ".join(str(p + 1) for p in pts)
        lines.append(f"  P{idx + 1}:  y = {a0:.4f} + {a1:.4f}·x")
        lines.append(f"      Точек ({len(pts)}): [{nums}]")
        lines.append("")

    lines.append("═══════════════════════════════════════")

    fig = Figure(figsize=(8.27, 11.69))
    ax = fig.add_subplot(111)
    ax.axis("off")
    ax.text(
        0.05,
        0.97,
        "\n".join(lines),
        va="top",
        ha="left",
        fontsize=10,
        family="monospace",
        transform=ax.transAxes,
    )
    pdf.savefig(fig)


def _write_image_page(pdf: PdfPages, image_path: Path) -> None:
    img = mpimg.imread(image_path)
    fig = Figure(figsize=(11.69, 8.27))
    ax = fig.add_subplot(111)
    ax.axis("off")
    ax.imshow(img)
    pdf.savefig(fig)
