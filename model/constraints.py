from pyomo.environ import *


def add_constraints(
    model,
    x,
    y,
    M,
    cluster_sizes=None
):

    # -----------------
    # (5) каждая точка ровно в один кластер
    # -----------------
    def assign_rule(model, k):
        return sum(
            model.sigma[k, j]
            for j in model.J
        ) == 1

    model.assign = Constraint(
        model.K,
        rule=assign_rule
    )


    # -----------------
    # (3)
    # -----------------
    def c1(model, k, j):
        return (
            model.a0[j]
            + model.a1[j] * x[k]
            - M * model.sigma[k, j]
            + model.u[k]
            >= y[k] - M
        )

    model.c1 = Constraint(
        model.K,
        model.J,
        rule=c1
    )


    # -----------------
    # (4)
    # -----------------
    def c2(model, k, j):
        return (
            model.a0[j]
            + model.a1[j] * x[k]
            + M * model.sigma[k, j]
            - model.u[k]
            <= y[k] + M
        )

    model.c2 = Constraint(
        model.K,
        model.J,
        rule=c2
    )


    # =========================================================
    # (9) РАЗМЕРЫ КЛАСТЕРОВ
    # =========================================================
    if cluster_sizes is not None:

        def size_rule(model, j):

            if cluster_sizes[j] is None:
                return Constraint.Skip

            return sum(
                model.sigma[k, j]
                for k in model.K
            ) == cluster_sizes[j]

        model.cluster_size = Constraint(
            model.J,
            rule=size_rule
        )