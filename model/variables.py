from pyomo.environ import *
from config import COEF_BOUND


def create_variables(model):

    # sigma_{k,j}
    model.sigma=Var(
        model.K,
        model.J,
        domain=Binary
    )

    # alpha0^j
    model.a0=Var(
        model.J,
        bounds=(-COEF_BOUND,COEF_BOUND)
    )

    # alpha1^j
    model.a1=Var(
        model.J,
        bounds=(-COEF_BOUND,COEF_BOUND)
    )

    # u_k >=0
    model.u=Var(
        model.K,
        domain=NonNegativeReals
    )