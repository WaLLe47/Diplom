"""Solution validation helpers."""

from typing import Any


def validate_solution(
    results: dict[str, Any],
    x: list[float],
    y: list[float],
    tolerance: float = 1e-6,
) -> bool:
    """Print and return whether reported MILP errors match real residuals."""
    print("\n=== ПРОВЕРКА ===")

    is_valid = True
    for cluster_index, point_indexes in results["clusters"].items():
        a0, a1 = results["coeffs"][cluster_index]

        for point_index in point_indexes:
            y_hat = a0 + a1 * x[point_index]
            real_error = abs(y[point_index] - y_hat)
            model_error = results["u"][point_index]

            print(
                f"k={point_index + 1}, "
                f"u={model_error:.6f}, "
                f"real={real_error:.6f}"
            )

            if abs(model_error - real_error) > tolerance:
                is_valid = False

    print("\nВалидация пройдена" if is_valid else "\nВНИМАНИЕ: несовпадение")
    return is_valid