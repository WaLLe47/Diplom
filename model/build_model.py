"""Factory for the cluster regression MILP model."""

from pyomo.environ import ConcreteModel, RangeSet

from config import BIG_M_MIN
from model.constraints import add_constraints
from model.objective import add_objective
from model.variables import create_variables


def _validate_inputs(
    x: list[float],
    y: list[float],
    r: int,
    cluster_sizes: list[int | None] | None,
) -> None:
    if len(x) != len(y):
        raise ValueError("Массивы x и y должны иметь одинаковую длину")
    if not x:
        raise ValueError("Набор данных не должен быть пустым")
    if r < 1:
        raise ValueError("Число кластеров должно быть положительным")
    if r > len(x):
        raise ValueError("Число кластеров не может превышать число точек")

    if cluster_sizes is None:
        return

    if len(cluster_sizes) != r:
        raise ValueError("Список размеров кластеров должен иметь длину r")

    fixed_sizes = [size for size in cluster_sizes if size is not None]
    if any(size < 0 for size in fixed_sizes):
        raise ValueError("Размеры кластеров не могут быть отрицательными")
    if sum(fixed_sizes) > len(x):
        raise ValueError("Сумма заданных размеров кластеров превышает число точек")


def build_model(
    x: list[float],
    y: list[float],
    r: int,
    cluster_sizes: list[int | None] | None = None,
) -> ConcreteModel:
    """Build and return an unsolved Pyomo MILP model."""
    _validate_inputs(x, y, r, cluster_sizes)

    model = ConcreteModel()
    model.K = RangeSet(0, len(x) - 1)
    model.J = RangeSet(0, r - 1)

    create_variables(model)
    add_objective(model)
    add_constraints(model, x, y, max(max(y) - min(y), BIG_M_MIN), cluster_sizes)

    return model