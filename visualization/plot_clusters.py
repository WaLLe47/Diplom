"""Plotly visualisations for cluster regression results."""

import colorsys
from typing import Any

import numpy as np
import plotly.graph_objects as go


def palette(n: int) -> list[dict[str, str]]:
    """Build a soft, visually distinct color palette for ``n`` clusters."""
    colors = []
    for i in range(n):
        hue = (i * 0.618) % 1
        red, green, blue = colorsys.hls_to_rgb(hue, 0.6, 0.65)
        colors.append(
            {
                "point": _rgb(red, green, blue, 255),
                "cross": _rgb(red, green, blue, 210),
                "line": _rgb(red, green, blue, 160),
            }
        )
    return colors


def _rgb(red: float, green: float, blue: float, scale: int) -> str:
    return f"rgb({int(red * scale)},{int(green * scale)},{int(blue * scale)})"


def build_cluster_plot(
    results: dict[str, Any],
    x: list[float],
    y: list[float],
    global_coeffs: tuple[float, float],
) -> go.Figure:
    """Build a chart with source points and fitted cluster regressions."""
    clusters = results["clusters"]
    coeffs = results["coeffs"]
    colors = palette(len(clusters))
    fig = go.Figure()

    for cluster_index, point_indexes in clusters.items():
        fig.add_trace(
            go.Scatter(
                x=[x[i] for i in point_indexes],
                y=[y[i] for i in point_indexes],
                mode="markers",
                name=f"Кластер {cluster_index + 1} (факт)",
                marker={"size": 8, "color": colors[cluster_index]["point"]},
            )
        )

    for cluster_index, point_indexes in clusters.items():
        a0, a1 = coeffs[cluster_index]
        fig.add_trace(
            go.Scatter(
                x=[x[i] for i in point_indexes],
                y=[a0 + a1 * x[i] for i in point_indexes],
                mode="markers",
                name=f"Кластер {cluster_index + 1} (модель)",
                marker={
                    "symbol": "x",
                    "size": 10,
                    "color": colors[cluster_index]["cross"],
                },
            )
        )

    x_line = np.linspace(min(x), max(x), 300)
    for cluster_index, (a0, a1) in enumerate(coeffs):
        fig.add_trace(
            go.Scatter(
                x=x_line,
                y=a0 + a1 * x_line,
                mode="lines",
                name=f"Регрессия кластер {cluster_index + 1}",
                line={"color": colors[cluster_index]["line"], "dash": "dash"},
            )
        )

    global_intercept, global_slope = global_coeffs
    fig.add_trace(
        go.Scatter(
            x=x_line,
            y=global_intercept + global_slope * x_line,
            mode="lines",
            name="Общая регрессия",
            line={"color": "rgb(80,80,80)", "width": 2},
        )
    )

    fig.update_layout(
        title="Кластерная линейная регрессия (MILP)",
        xaxis_title="Инвестиции (x)",
        yaxis_title="Выпуск продукции (y)",
        template="plotly_white",
        legend={"title": "Обозначения"},
    )
    fig.update_xaxes(showgrid=True, gridcolor="LightGray")
    fig.update_yaxes(showgrid=True, gridcolor="LightGray")
    return fig


def build_error_plot(results: dict[str, Any], x: list[float], y: list[float]) -> go.Figure:
    """Build a chart comparing factual and calculated values by point."""
    clusters = results["clusters"]
    coeffs = results["coeffs"]
    colors = palette(len(clusters))
    fig = go.Figure()

    all_points = []
    for cluster_index, point_indexes in clusters.items():
        a0, a1 = coeffs[cluster_index]
        for point_index in point_indexes:
            all_points.append(
                {
                    "x": x[point_index],
                    "y_fact": y[point_index],
                    "y_calc": a0 + a1 * x[point_index],
                    "cluster": cluster_index,
                }
            )
    all_points.sort(key=lambda point: point["x"])

    fig.add_trace(
        go.Scatter(
            x=[point["x"] for point in all_points],
            y=[point["y_fact"] for point in all_points],
            mode="lines",
            name="Фактические значения",
            line={"color": "black", "width": 2},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[point["x"] for point in all_points],
            y=[point["y_calc"] for point in all_points],
            mode="lines",
            name="Расчётные значения",
            line={"color": "gray", "dash": "dot", "width": 2},
        )
    )

    for cluster_index, point_indexes in clusters.items():
        fig.add_trace(
            go.Scatter(
                x=[x[i] for i in point_indexes],
                y=[y[i] for i in point_indexes],
                mode="markers",
                name=f"Кластер {cluster_index + 1} факт",
                marker={"size": 9, "color": colors[cluster_index]["point"]},
            )
        )

        a0, a1 = coeffs[cluster_index]
        fig.add_trace(
            go.Scatter(
                x=[x[i] for i in point_indexes],
                y=[a0 + a1 * x[i] for i in point_indexes],
                mode="markers",
                name=f"Кластер {cluster_index + 1} расчёт",
                marker={
                    "symbol": "x",
                    "size": 10,
                    "color": colors[cluster_index]["cross"],
                },
            )
        )

    for point in all_points:
        color = colors[point["cluster"]]["line"]
        fig.add_trace(
            go.Scatter(
                x=[point["x"], point["x"]],
                y=[point["y_fact"], point["y_calc"]],
                mode="lines",
                showlegend=False,
                line={"color": color, "width": 1.5},
            )
        )

    fig.update_layout(
        title="Фактические и расчётные значения с ошибками",
        xaxis_title="Инвестиции (x)",
        yaxis_title="Выпуск продукции (y)",
        template="plotly_white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="LightGray")
    fig.update_yaxes(showgrid=True, gridcolor="LightGray")
    return fig
