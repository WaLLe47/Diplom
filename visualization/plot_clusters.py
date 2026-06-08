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


def _base_layout(title: str, x_title: str, y_title: str) -> dict:
    """Shared Plotly layout tuned for the white chart canvas."""
    return dict(
        title=dict(text=title, font=dict(size=16, color="#2e1065")),
        xaxis_title=x_title,
        yaxis_title=y_title,
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="Segoe UI, system-ui, sans-serif", color="#4c1d95", size=12),
        margin=dict(l=64, r=24, t=56, b=52),
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#e9d5ff",
            borderwidth=1,
            font=dict(size=11),
        ),
    )


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
        a0, a1_list = coeffs[cluster_index]
        a1 = a1_list[0]  # first feature for 2-D plot
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
    for cluster_index, (a0, a1_list) in enumerate(coeffs):
        a1 = a1_list[0]
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

    layout = _base_layout(
        "Кластерная линейная регрессия (MILP)",
        "x",
        "y",
    )
    layout["legend"]["title"] = {"text": "Обозначения"}
    fig.update_layout(**layout)
    fig.update_xaxes(showgrid=True, gridcolor="#eef2f7", zerolinecolor="#cbd5e1")
    fig.update_yaxes(showgrid=True, gridcolor="#eef2f7", zerolinecolor="#cbd5e1")
    return fig


def build_error_plot(results: dict[str, Any], x: list[float], y: list[float]) -> go.Figure:
    """Build a chart comparing factual and calculated values by point."""
    clusters = results["clusters"]
    coeffs = results["coeffs"]
    colors = palette(len(clusters))
    fig = go.Figure()

    all_points = []
    for cluster_index, point_indexes in clusters.items():
        a0, a1_list = coeffs[cluster_index]
        a1_0 = a1_list[0]
        for point_index in point_indexes:
            all_points.append(
                {
                    "x": x[point_index],
                    "y_fact": y[point_index],
                    "y_calc": a0 + a1_0 * x[point_index],
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

        a0, a1_list = coeffs[cluster_index]
        a1_0 = a1_list[0]
        fig.add_trace(
            go.Scatter(
                x=[x[i] for i in point_indexes],
                y=[a0 + a1_0 * x[i] for i in point_indexes],
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
        **_base_layout(
            "Фактические и расчётные значения с ошибками",
            "x",
            "y",
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor="#eef2f7", zerolinecolor="#cbd5e1")
    fig.update_yaxes(showgrid=True, gridcolor="#eef2f7", zerolinecolor="#cbd5e1")
    return fig