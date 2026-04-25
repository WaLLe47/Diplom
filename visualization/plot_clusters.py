import matplotlib.pyplot as plt
import numpy as np


def plot_clusters(results, x, y, ax=None, show=True):
    colors = [
        "red",
        "blue",
        "green",
        "orange",
        "purple",
        "brown",
        "cyan",
        "magenta",
    ]

    if ax is None:
        _, ax = plt.subplots()

    clusters = results["clusters"]
    coeffs = results["coeffs"]

    for j, pts in clusters.items():
        xs = []
        ys = []

        for k in pts:
            xs.append(x[k])
            ys.append(y[k])

        color = colors[j % len(colors)]

        ax.scatter(xs, ys, color=color, label=f"Cluster {j + 1}")

    xline = np.linspace(min(x), max(x), 200)

    for j, (a0, a1) in enumerate(coeffs):
        yline = a0 + a1 * xline
        color = colors[j % len(colors)]

        ax.plot(xline, yline, linestyle="--", color=color, label=f"Reg {j + 1}")

    ax.grid(True)
    ax.legend()
    ax.set_title("Cluster Linear Regression")

    if show:
        plt.show()

    return ax