"""Pyomo decision variables for the cluster regression model."""

from pyomo.environ import Binary, NonNegativeReals, Var

from config import COEF_BOUND


def create_variables(model, p: int) -> None:
    """Attach assignment, coefficient and absolute-error variables.

    Parameters
    ----------
    model : ConcreteModel
    p     : number of predictor columns (X features)
    """
    model.sigma = Var(model.K, model.J, domain=Binary)
    # a0[j] — intercept for cluster j
    model.a0 = Var(model.J, bounds=(-COEF_BOUND, COEF_BOUND))
    # a1[j, f] — coefficient for cluster j, feature f  (0 … p-1)
    model.F = range(p)
    model.a1 = Var(model.J, model.F, bounds=(-COEF_BOUND, COEF_BOUND))
    model.u = Var(model.K, domain=NonNegativeReals)