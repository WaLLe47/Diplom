from pyomo.environ import SolverFactory
from config import SOLVER_NAME


def solve_model(model):

    solver=SolverFactory(
        SOLVER_NAME
    )

    result=solver.solve(
        model,
        tee=False
    )

    return result