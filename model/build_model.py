"""Factory for the cluster regression MILP model."""

from pyomo.environ import ConcreteModel, RangeSet

from config import BIG_M_MIN
from model.constraints import add_constraints
from model.objective import add_objective
from model.variables import create_variables


def _validate_inputs(
    X: list[list[float]],
    y: list[float],
    r: int,
    cluster_sizes: list[int | None] | None,
) -> None:
    if len(X) != len(y):
        raise ValueError("Массивы X и y должны иметь одинаковую длину")
    if not X:
        raise ValueError("Набор данных не должен быть пустым")
    if r < 1:
        raise ValueError("Число кластеров должно быть положительным")
    if r > len(X):
        raise ValueError("Число кластеров не может превышать число точек")

    if cluster_sizes is None:
        return
    if len(cluster_sizes) != r:
        raise ValueError("Список размеров кластеров должен иметь длину r")
    fixed = [s for s in cluster_sizes if s is not None]
    if any(s < 0 for s in fixed):
        raise ValueError("Размеры кластеров не могут быть отрицательными")
    if sum(fixed) > len(X):
        raise ValueError("Сумма заданных размеров превышает число точек")


def build_model(
    X: list[list[float]],          # rows = observations, cols = features
    y: list[float],
    r: int,
    cluster_sizes: list[int | None] | None = None,
) -> ConcreteModel:
    """Build and return an unsolved Pyomo MILP model."""
    _validate_inputs(X, y, r, cluster_sizes)

    p = len(X[0])          # number of predictors

    model = ConcreteModel()
    model.K = RangeSet(0, len(X) - 1)
    model.J = RangeSet(0, r - 1)

    create_variables(model, p)
    add_objective(model)
    add_constraints(model, X, y, max(max(y) - min(y), BIG_M_MIN), cluster_sizes)

    return model