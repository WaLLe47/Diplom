import matplotlib.pyplot as plt
import numpy as np


def plot_clusters(
    results,
    x,
    y
):

    colors=[
        "red",
        "blue",
        "green",
        "orange",
        "purple"
    ]

    plt.figure()

    clusters=results["clusters"]
    coeffs=results["coeffs"]


    for j,pts in clusters.items():

        xs=[]
        ys=[]

        for k in pts:
            xs.append(x[k])
            ys.append(y[k])

        plt.scatter(
            xs,
            ys,
            color=colors[j],
            label=f"Cluster {j+1}"
        )


    xline=np.linspace(
        min(x),
        max(x),
        200
    )

    for j,(a0,a1) in enumerate(coeffs):

        yline=a0+a1*xline

        plt.plot(
            xline,
            yline,
            linestyle="--",
            color=colors[j],
            label=f"Reg {j+1}"
        )

    plt.grid(True)
    plt.legend()
    plt.title(
      "Cluster Linear Regression"
    )
    plt.show()