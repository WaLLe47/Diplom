from pyomo.environ import *

from model.variables import create_variables
from model.objective import add_objective
from model.constraints import add_constraints


def build_model(
    x,
    y,
    r,
    cluster_sizes=None
):

    n = len(x)

    M = max(y) - min(y)

    model = ConcreteModel()

    model.K = RangeSet(0, n - 1)
    model.J = RangeSet(0, r - 1)

    create_variables(model)
    add_objective(model)

    add_constraints(
        model,
        x,
        y,
        M,
        cluster_sizes
    )

    return model