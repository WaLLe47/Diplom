"""Objective function for the cluster regression MILP."""

from pyomo.environ import Objective, minimize


def add_objective(model) -> None:
    """Minimise the sum of absolute approximation errors."""
    model.obj = Objective(expr=sum(model.u[k] for k in model.K), sense=minimize)