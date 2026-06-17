"""Helpers for converting a solved Pyomo model to plain Python data."""

from typing import Any

from pyomo.environ import value


def extract_results(
    model: Any,
    X: list[list[float]],
    y: list[float],
    r: int,
) -> dict[str, Any]:
    """Extract clusters, regression coefficients and absolute errors."""
    p = len(X[0])
    clusters = {j: [] for j in range(r)}

    for k in range(len(X)):
        for j in range(r):
            if value(model.sigma[k, j]) > 0.5:
                clusters[j].append(k)

    # coeffs[j] = (a0, [a1_0, a1_1, ...])
    coeffs = [
        (value(model.a0[j]), [value(model.a1[j, f]) for f in range(p)])
        for j in range(r)
    ]
    errors = [value(model.u[k]) for k in range(len(y))]

    return {"clusters": clusters, "coeffs": coeffs, "u": errors}