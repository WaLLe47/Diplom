from pyomo.environ import *


def add_objective(model):

    # min Σu_k (МНМ)
    model.obj=Objective(
        expr=sum(
            model.u[k]
            for k in model.K
        ),
        sense=minimize
    )