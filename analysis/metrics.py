"""Metrics for evaluating regression quality."""


def mean_percent_error(y: list[float], u: list[float]) -> float:
    """Return mean absolute percentage error: 100 * Σu / Σy.

    Args:
        y: Observed values.
        u: Absolute approximation errors from the MILP model.

    Returns:
        Error as a percentage (0–100+).

    Raises:
        ValueError: If ``y`` is empty or its sum is zero.
    """
    if not y:
        raise ValueError("Массив y не может быть пустым")
    total_y = sum(y)
    if total_y == 0:
        raise ValueError("Сумма y равна нулю — невозможно вычислить ошибку")
    return 100.0 * sum(u) / total_y
