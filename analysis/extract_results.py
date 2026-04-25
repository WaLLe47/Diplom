from pyomo.environ import value


def extract_results(
    model,
    x,
    y,
    r
):

    clusters={j:[] for j in range(r)}

    for k in range(len(x)):
        for j in range(r):

            if value(
                model.sigma[k,j]
            )>0.5:
                clusters[j].append(k)


    coeffs=[]

    for j in range(r):

        coeffs.append(
            (
                value(model.a0[j]),
                value(model.a1[j])
            )
        )


    u=[
        value(model.u[k])
        for k in range(len(x))
    ]


    return {
        "clusters":clusters,
        "coeffs":coeffs,
        "u":u
    }