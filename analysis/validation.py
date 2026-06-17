"""Solution validation helpers."""

from typing import Any


def validate_solution(
    results: dict[str, Any],
    x: list[float],
    y: list[float],
    tolerance: float = 1e-6,
) -> tuple[bool, list[str]]:
    """Verify that reported MILP errors match real regression residuals.

    Args:
        results: Output of :func:`extract_results`.
        x: Input feature values.
        y: Target values.
        tolerance: Maximum allowed discrepancy between model and real error.

    Returns:
        Tuple of (is_valid, list_of_warning_strings).
    """
    warnings: list[str] = []

    for cluster_index, point_indexes in results["clusters"].items():
        a0, a1 = results["coeffs"][cluster_index]
        for point_index in point_indexes:
            y_hat = a0 + a1 * x[point_index]
            real_error = abs(y[point_index] - y_hat)
            model_error = results["u"][point_index]
            if abs(model_error - real_error) > tolerance:
                warnings.append(
                    f"k={point_index + 1}: model_err={model_error:.6f}, "
                    f"real_err={real_error:.6f}, diff={abs(model_error - real_error):.2e}"
                )

    return len(warnings) == 0, warnings
