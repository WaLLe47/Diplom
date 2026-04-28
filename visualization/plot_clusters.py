import colorsys

import numpy as np
import plotly.graph_objects as go


def palette(n):
    out = []
    for i in range(n):
        h = (i * 0.618) % 1
        r_, g_, b_ = colorsys.hls_to_rgb(h, 0.6, 0.65)

        out.append(
            {
                "point": f"rgb({int(r_ * 255)},{int(g_ * 255)},{int(b_ * 255)})",
                "cross": f"rgb({int(r_ * 210)},{int(g_ * 210)},{int(b_ * 210)})",
                "line": f"rgb({int(r_ * 160)},{int(g_ * 160)},{int(b_ * 160)})",
            }
        )
    return out


def build_cluster_plot(results, x, y, global_coeffs):
    clusters = results["clusters"]
    coeffs = results["coeffs"]
    r = len(clusters)
    colors = palette(r)

    fig = go.Figure()

    for j in range(r):
        xs = [x[i] for i in clusters[j]]
        ys = [y[i] for i in clusters[j]]

        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers",
                name=f"Кластер {j + 1} (факт)",
                marker=dict(size=8, color=colors[j]["point"]),
            )
        )

    for j in range(r):
        a0, a1 = coeffs[j]
        xs = [x[i] for i in clusters[j]]
        ys = [a0 + a1 * x[i] for i in clusters[j]]

        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers",
                name=f"Кластер {j + 1} (модель)",
                marker=dict(symbol="x", size=10, color=colors[j]["cross"]),
            )
        )

    x_line = np.linspace(min(x), max(x), 300)

    for j in range(r):
        a0, a1 = coeffs[j]
        fig.add_trace(
            go.Scatter(
                x=x_line,
                y=a0 + a1 * x_line,
                mode="lines",
                name=f"Регрессия кластер {j + 1}",
                line=dict(color=colors[j]["line"], dash="dash"),
            )
        )

    g0, g1 = global_coeffs
    fig.add_trace(
        go.Scatter(
            x=x_line,
            y=g0 + g1 * x_line,
            mode="lines",
            name="Общая регрессия",
            line=dict(color="rgb(80,80,80)", width=2),
        )
    )

    fig.update_layout(
        title="Кластерная линейная регрессия (MILP)",
        xaxis_title="Инвестиции (x)",
        yaxis_title="Выпуск продукции (y)",
        template="plotly_white",
        legend=dict(title="Обозначения"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="LightGray")
    fig.update_yaxes(showgrid=True, gridcolor="LightGray")

    return fig


def build_error_plot(results, x, y):
    clusters = results["clusters"]
    coeffs = results["coeffs"]
    r = len(clusters)
    colors = palette(r)

    fig = go.Figure()

    all_points = []
    for j in range(r):
        a0, a1 = coeffs[j]
        for i in clusters[j]:
            all_points.append(
                {
                    "x": x[i],
                    "y_fact": y[i],
                    "y_calc": a0 + a1 * x[i],
                    "cluster": j,
                }
            )

    all_points = sorted(all_points, key=lambda p: p["x"])

    x_all = [p["x"] for p in all_points]
    y_fact_all = [p["y_fact"] for p in all_points]
    y_calc_all = [p["y_calc"] for p in all_points]

    fig.add_trace(
        go.Scatter(
            x=x_all,
            y=y_fact_all,
            mode="lines",
            name="Фактические значения",
            line=dict(color="black", width=2),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x_all,
            y=y_calc_all,
            mode="lines",
            name="Расчётные значения",
            line=dict(color="gray", dash="dot", width=2),
        )
    )

    for j in range(r):
        xs = [x[i] for i in clusters[j]]
        ys_fact = [y[i] for i in clusters[j]]
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys_fact,
                mode="markers",
                name=f"Кластер {j + 1} факт",
                marker=dict(size=9, color=colors[j]["point"]),
            )
        )

    for j in range(r):
        a0, a1 = coeffs[j]
        xs = [x[i] for i in clusters[j]]
        ys_calc = [a0 + a1 * x[i] for i in clusters[j]]
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys_calc,
                mode="markers",
                name=f"Кластер {j + 1} расчёт",
                marker=dict(symbol="x", size=10, color=colors[j]["cross"]),
            )
        )

    for p in all_points:
        j = p["cluster"]
        fig.add_trace(
            go.Scatter(
                x=[p["x"], p["x"]],
                y=[p["y_fact"], p["y_calc"]],
                mode="lines",
                showlegend=False,
                line=dict(color=colors[j]["line"], width=1.5),
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
