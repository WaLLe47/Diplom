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


def _as_matrix(X: list[Any]) -> list[list[float]]:
    """Return ``X`` as a 2-D matrix; keep compatibility with old 1-D calls."""
    if not X:
        return []
    if isinstance(X[0], (list, tuple)):
        return [list(row) for row in X]
    return [[value] for value in X]


def _predict(a0: float, a1_list: list[float], row: list[float]) -> float:
    """Calculate fitted y for one observation using all available features."""
    return a0 + sum(a * x for a, x in zip(a1_list, row))


def _point_numbers(X_matrix: list[list[float]]) -> list[int]:
    """Return 1-based observation numbers for plots that must show every row."""
    return list(range(1, len(X_matrix) + 1))


def _x_values_for_cluster_plot(
    X_matrix: list[list[float]],
) -> tuple[list[float | int], str, bool]:
    """Choose the cluster plot X axis.

    A single-factor regression can be drawn against the actual factor value. For
    a multivariate model there is no honest 2-D regression line, so we use the
    observation number to avoid hiding rows behind one projected ``x1`` axis.
    """
    is_multivariate = bool(X_matrix and len(X_matrix[0]) > 1)
    if is_multivariate:
        return _point_numbers(X_matrix), "№ наблюдения", True
    return [row[0] for row in X_matrix], "x", False


def _hover_text(point_index: int, row: list[float], x_cols: list[str] | None) -> str:
    """Build compact hover text with all X values for a source observation."""
    parts = [f"Наблюдение: {point_index + 1}"]
    for feature_index, value in enumerate(row):
        name = (
            x_cols[feature_index]
            if x_cols and feature_index < len(x_cols)
            else f"x{feature_index + 1}"
        )
        parts.append(f"{name}: {value:g}")
    return "<br>".join(parts)


def build_cluster_plot(
    results: dict[str, Any],
    X: list[Any],
    y: list[float],
    global_coeffs: tuple[float, float],
    x_cols: list[str] | None = None,
) -> go.Figure:
    """Build a chart with source points and fitted cluster regressions."""
    X_matrix = _as_matrix(X)
    x_axis, x_axis_title, is_multivariate = _x_values_for_cluster_plot(X_matrix)
    clusters = results["clusters"]
    coeffs = results["coeffs"]
    colors = palette(len(clusters))
    fig = go.Figure()

    for cluster_index, point_indexes in clusters.items():
        fig.add_trace(
            go.Scatter(
                x=[x_axis[i] for i in point_indexes],
                y=[y[i] for i in point_indexes],
                mode="markers",
                name=f"Кластер {cluster_index + 1} (факт)",
                marker={"size": 8, "color": colors[cluster_index]["point"]},
                text=[_hover_text(i, X_matrix[i], x_cols) for i in point_indexes],
                hovertemplate="%{text}<br>Факт y: %{y}<extra></extra>",
            )
        )

    for cluster_index, point_indexes in clusters.items():
        a0, a1_list = coeffs[cluster_index]
        fig.add_trace(
            go.Scatter(
                x=[x_axis[i] for i in point_indexes],
                y=[_predict(a0, a1_list, X_matrix[i]) for i in point_indexes],
                mode="markers",
                name=f"Кластер {cluster_index + 1} (модель)",
                marker={
                    "symbol": "x",
                    "size": 10,
                    "color": colors[cluster_index]["cross"],
                },
                text=[_hover_text(i, X_matrix[i], x_cols) for i in point_indexes],
                hovertemplate="%{text}<br>Расчёт y: %{y}<extra></extra>",
            )
        )

    if not is_multivariate and x_axis:
        x_line = np.linspace(min(x_axis), max(x_axis), 300)
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

    title = "Кластерная линейная регрессия (MILP)"
    if is_multivariate:
        title += " — прогноз по всем X, ось по наблюдениям"
    layout = _base_layout(
        title,
        x_axis_title if is_multivariate else (x_cols[0] if x_cols else x_axis_title),
        "y",
    )
    layout["legend"]["title"] = {"text": "Обозначения"}
    fig.update_layout(**layout)
    fig.update_xaxes(showgrid=True, gridcolor="#eef2f7", zerolinecolor="#cbd5e1")
    fig.update_yaxes(showgrid=True, gridcolor="#eef2f7", zerolinecolor="#cbd5e1")
    return fig


def build_error_plot(results: dict[str, Any], X: list[Any], y: list[float]) -> go.Figure:
    """Build a chart comparing factual and calculated values by observation."""
    X_matrix = _as_matrix(X)
    clusters = results["clusters"]
    coeffs = results["coeffs"]
    colors = palette(len(clusters))
    fig = go.Figure()

    all_points = []
    for cluster_index, point_indexes in clusters.items():
        a0, a1_list = coeffs[cluster_index]
        for point_index in point_indexes:
            all_points.append(
                {
                    "x": point_index + 1,
                    "y_fact": y[point_index],
                    "y_calc": _predict(a0, a1_list, X_matrix[point_index]),
                    "cluster": cluster_index,
                }
            )
    all_points.sort(key=lambda point: point["x"])

    fig.add_trace(
        go.Scatter(
            x=[point["x"] for point in all_points],
            y=[point["y_fact"] for point in all_points],
            mode="lines+markers",
            name="Фактические значения",
            line={"color": "black", "width": 2},
            marker={"size": 5, "color": "black"},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[point["x"] for point in all_points],
            y=[point["y_calc"] for point in all_points],
            mode="lines+markers",
            name="Расчётные значения",
            line={"color": "gray", "dash": "dot", "width": 2},
            marker={"size": 5, "color": "gray"},
        )
    )

    for cluster_index, point_indexes in clusters.items():
        fig.add_trace(
            go.Scatter(
                x=[i + 1 for i in point_indexes],
                y=[y[i] for i in point_indexes],
                mode="markers",
                name=f"Кластер {cluster_index + 1} факт",
                marker={"size": 9, "color": colors[cluster_index]["point"]},
            )
        )

        a0, a1_list = coeffs[cluster_index]
        fig.add_trace(
            go.Scatter(
                x=[i + 1 for i in point_indexes],
                y=[_predict(a0, a1_list, X_matrix[i]) for i in point_indexes],
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
            "№ наблюдения",
            "y",
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor="#eef2f7", zerolinecolor="#cbd5e1")
    fig.update_yaxes(showgrid=True, gridcolor="#eef2f7", zerolinecolor="#cbd5e1")
    return fig