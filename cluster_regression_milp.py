from pyomo.environ import *

# -----------------------------
# ДАННЫЕ
# -----------------------------
x = [
    10,12,15,18,20,
    23,25,28,30,33,
    35,37,40,42,45,
    47,50,52
]

y = [
    300,350,420,480,520,
    590,640,710,760,820,
    870,920,980,1030,1100,
    1150,1210,1260
]

n = len(x)
r = 3

# -----------------------------
# Big-M (нормальный выбор)
# -----------------------------
M = max(y) - min(y)

cluster1_size = None  # можно задать число

# -----------------------------
# МОДЕЛЬ
# -----------------------------
model = ConcreteModel()

model.K = RangeSet(0, n-1)
model.J = RangeSet(0, r-1)

# -----------------------------
# ПЕРЕМЕННЫЕ
# -----------------------------
model.sigma = Var(model.K, model.J, domain=Binary)

model.a0 = Var(model.J, bounds=(-1e6, 1e6))
model.a1 = Var(model.J, bounds=(-1e6, 1e6))

model.u = Var(model.K, domain=NonNegativeReals)

# -----------------------------
# ЦЕЛЬ
# -----------------------------
model.obj = Objective(
    expr=sum(model.u[k] for k in model.K),
    sense=minimize
)

# -----------------------------
# ОГРАНИЧЕНИЯ
# -----------------------------
def assign_rule(model, k):
    return sum(model.sigma[k, j] for j in model.J) == 1

model.assign = Constraint(model.K, rule=assign_rule)

# -----------------------------
# Big-M (нижняя граница)
# -----------------------------
def c1(model, k, j):
    return (
        model.a0[j] + model.a1[j]*x[k]
        - M*model.sigma[k, j]
        + model.u[k]
        >= y[k] - M
    )

model.c1 = Constraint(model.K, model.J, rule=c1)

# -----------------------------
# Big-M (верхняя граница)
# -----------------------------
def c2(model, k, j):
    return (
        model.a0[j] + model.a1[j]*x[k]
        + M*model.sigma[k, j]
        - model.u[k]
        <= y[k] + M
    )

model.c2 = Constraint(model.K, model.J, rule=c2)

# -----------------------------
# ограничение размеров (если нужно)
# -----------------------------
if cluster1_size is not None:
    model.size = Constraint(
        expr=sum(model.sigma[k, 0] for k in model.K) == cluster1_size
    )

# -----------------------------
# РЕШЕНИЕ
# -----------------------------
solver = SolverFactory("appsi_highs")
solver.solve(model)

# -----------------------------
# КЛАСТЕРЫ
# -----------------------------
clusters = {j: [] for j in range(r)}

for k in range(n):
    for j in range(r):
        if value(model.sigma[k, j]) > 0.5:
            clusters[j].append(k+1)

print("\n=== КЛАСТЕРЫ ===")
for j in clusters:
    print(f"P{j+1} =", clusters[j])

# -----------------------------
# МОДЕЛИ
# -----------------------------
print("\n=== МОДЕЛИ ===")
for j in range(r):
    print(
        f"Кластер {j+1}: y = "
        f"{value(model.a0[j]):.4f} + "
        f"{value(model.a1[j]):.4f} x"
    )

# -----------------------------
# ОШИБКА
# -----------------------------
sum_u = sum(max(0, value(model.u[k])) for k in model.K)
sum_y = sum(y)

E = 100 * sum_u / sum_y

print("\n=== ТОЧНОСТЬ ===")
print(f"E = {E:.4f}%")

# -----------------------------
# ПОТОЧЕЧНЫЕ ОШИБКИ
# -----------------------------
print("\n=== ОШИБКИ ===")
for k in range(n):
    print(k+1, max(0, value(model.u[k])))

# -----------------------------
# ПРОВЕРКА МОДЕЛИ (ВАЖНО)
# -----------------------------
print("\n=== ПРОВЕРКА ===")

for j in range(r):

    a0 = value(model.a0[j])
    a1 = value(model.a1[j])

    for k in clusters[j]:

        i = k - 1

        y_hat = a0 + a1 * x[i]

        real_error = abs(y[i] - y_hat)

        print(
            f"k={k}, u={value(model.u[i]):.4f}, "
            f"real={real_error:.4f}"
        )
#_____________________________________________________________________
import matplotlib.pyplot as plt
import numpy as np

plt.figure()

colors = ["red", "blue", "green", "orange"]

# ------------------------
# точки по кластерам
# ------------------------
for j in range(r):
    xs = []
    ys = []

    for k in clusters[j]:
        i = k - 1
        xs.append(x[i])
        ys.append(y[i])

    plt.scatter(xs, ys, color=colors[j], label=f"Cluster {j+1}")

# ------------------------
# линии регрессии
# ------------------------
x_line = np.linspace(min(x), max(x), 100)

for j in range(r):
    a0 = value(model.a0[j])
    a1 = value(model.a1[j])

    y_line = a0 + a1 * x_line

    plt.plot(
        x_line,
        y_line,
        color=colors[j],
        linestyle="--",
        label=f"Regression {j+1}"
    )

plt.xlabel("x")
plt.ylabel("y")
plt.title("Clustered Linear Regression (MILP)")
plt.legend()
plt.grid(True)

plt.show()