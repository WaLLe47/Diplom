"""Constraints for the cluster regression MILP."""

from pyomo.environ import Constraint


def add_constraints(
    model,
    x: list[float],
    y: list[float],
    big_m: float,
    cluster_sizes: list[int | None] | None = None,
) -> None:
    """Attach assignment, Big-M approximation and optional size constraints."""

    def assign_rule(model, k):
        return sum(model.sigma[k, j] for j in model.J) == 1

    model.assign = Constraint(model.K, rule=assign_rule)

    def lower_error_bound(model, k, j):
        return (
            model.a0[j]
            + model.a1[j] * x[k]
            - big_m * model.sigma[k, j]
            + model.u[k]
            >= y[k] - big_m
        )

    model.lower_error_bound = Constraint(model.K, model.J, rule=lower_error_bound)

    def upper_error_bound(model, k, j):
        return (
            model.a0[j]
            + model.a1[j] * x[k]
            + big_m * model.sigma[k, j]
            - model.u[k]
            <= y[k] + big_m
        )

    model.upper_error_bound = Constraint(model.K, model.J, rule=upper_error_bound)

    if cluster_sizes is not None:

        def size_rule(model, j):
            if cluster_sizes[j] is None:
                return Constraint.Skip
            return sum(model.sigma[k, j] for k in model.K) == cluster_sizes[j]

        model.cluster_size = Constraint(model.J, rule=size_rule)
