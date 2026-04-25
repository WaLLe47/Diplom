import math


def validate_solution(
    results,
    x,
    y
):

    print("\n=== ПРОВЕРКА ===")

    clusters=results["clusters"]
    coeffs=results["coeffs"]
    u=results["u"]

    tol=1e-6

    ok=True

    for j,pts in clusters.items():

        a0,a1=coeffs[j]

        for k in pts:

            yhat=a0+a1*x[k]

            real_error=abs(
                y[k]-yhat
            )

            print(
                f"k={k+1}, "
                f"u={u[k]:.6f}, "
                f"real={real_error:.6f}"
            )

            if abs(
               u[k]-real_error
            )>tol:
                ok=False

    if ok:
        print("\nВалидация пройдена")
    else:
        print("\nВНИМАНИЕ: несовпадение")