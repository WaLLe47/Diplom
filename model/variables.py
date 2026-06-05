"""Pyomo decision variables for the cluster regression model."""

from pyomo.environ import Binary, NonNegativeReals, Var

from config import COEF_BOUND


def create_variables(model) -> None:
    """Attach assignment, coefficient and absolute-error variables."""
    model.sigma = Var(model.K, model.J, domain=Binary)
    model.a0 = Var(model.J, bounds=(-COEF_BOUND, COEF_BOUND))
    model.a1 = Var(model.J, bounds=(-COEF_BOUND, COEF_BOUND))
    model.u = Var(model.K, domain=NonNegativeReals)