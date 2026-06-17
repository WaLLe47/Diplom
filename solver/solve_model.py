"""Solver wrapper with consistent status validation."""

from pyomo.environ import SolverFactory, TerminationCondition

from config import SOLVER_NAME

_ACCEPTABLE_TERMINATIONS = {
    TerminationCondition.optimal,
    TerminationCondition.feasible,
}


def solve_model(model):
    """Solve a Pyomo model and raise a clear error on solver failure."""
    solver = SolverFactory(SOLVER_NAME)
    if not solver.available():
        raise RuntimeError(f"Солвер недоступен: {SOLVER_NAME}")

    result = solver.solve(model, tee=False)
    termination = result.solver.termination_condition
    if termination not in _ACCEPTABLE_TERMINATIONS:
        raise RuntimeError(f"Оптимизационная задача не решена: {termination}")

    return result