# ============================================================
# 📦 БИБЛИОТЕКИ
# ============================================================
from pyomo.environ import *
import plotly.graph_objects as go
import numpy as np
from sklearn.linear_model import LinearRegression
import colorsys


# ============================================================
# 📊 ИСХОДНЫЕ ДАННЫЕ (x = инвестиции, y = выпуск)
# ============================================================
x = [
    29.8,37,56.8,78.4,105.9,
    135.6,110.1,112.9,162.6,212.3,
    224.9,261.5,362.8,367.8,424.8,
    484.6,472.2,480.6,550.5,731.3
]

y = [
    453565,571186,672332,764300,944965,
    1312181,1061672,1427273,1812752,1941784,
    1886216,2102321,2766834,2770635,2742593,
    3265833,3280446,3535705,5263682,5962482
]

n = len(x)   # количество наблюдений
r = 2        # число кластеров (режимов экономики)

# Big-M параметр (важен для MILP)
M = max(y) - min(y)


# ============================================================
# 🧠 ПОСТРОЕНИЕ МОДЕЛИ КЛАСТЕРНОЙ ЛИНЕЙНОЙ РЕГРЕССИИ (MILP)
# ============================================================
model = ConcreteModel()

# индексы:
# K — наблюдения
# J — кластеры
model.K = RangeSet(0, n-1)
model.J = RangeSet(0, r-1)


# ============================================================
# 🔧 ПЕРЕМЕННЫЕ МОДЕЛИ
# ============================================================

# sigma[k,j] = 1 если точка k принадлежит кластеру j
model.sigma = Var(model.K, model.J, domain=Binary)

# параметры линейной модели y = a0 + a1*x для каждого кластера
model.a0 = Var(model.J)
model.a1 = Var(model.J)

# u_k = ошибка аппроксимации (модуль ошибки через MILP)
model.u = Var(model.K, domain=NonNegativeReals)


# ============================================================
# 🎯 ЦЕЛЕВАЯ ФУНКЦИЯ
# минимизируем сумму ошибок по всем точкам
# ============================================================
model.obj = Objective(
    expr=sum(model.u[k] for k in model.K),
    sense=minimize
)


# ============================================================
# 📌 ОГРАНИЧЕНИЕ: каждая точка принадлежит ровно одному кластеру
# ============================================================
def assign_rule(model, k):
    return sum(model.sigma[k, j] for j in model.J) == 1

model.assign = Constraint(model.K, rule=assign_rule)


# ============================================================
# 📌 ЛИНЕЙНАЯ АППРОКСИМАЦИЯ (Big-M)
# нижняя граница ошибки
# ============================================================
def c1(model, k, j):
    return (
        model.a0[j] + model.a1[j]*x[k]
        - M*model.sigma[k, j]
        + model.u[k]
        >= y[k] - M
    )

model.c1 = Constraint(model.K, model.J, rule=c1)


# ============================================================
# 📌 ЛИНЕЙНАЯ АППРОКСИМАЦИЯ (Big-M)
# верхняя граница ошибки
# ============================================================
def c2(model, k, j):
    return (
        model.a0[j] + model.a1[j]*x[k]
        + M*model.sigma[k, j]
        - model.u[k]
        <= y[k] + M
    )

model.c2 = Constraint(model.K, model.J, rule=c2)


# ============================================================
# 🚀 РЕШЕНИЕ ЗАДАЧИ ОПТИМИЗАЦИИ
# ============================================================
SolverFactory("appsi_highs").solve(model)


# ============================================================
# 📦 ФОРМИРОВАНИЕ КЛАСТЕРОВ ПО sigma
# ============================================================
clusters = {j: [] for j in range(r)}

for k in range(n):
    for j in range(r):
        if value(model.sigma[k, j]) > 0.5:
            clusters[j].append(k)


print("\n=== КЛАСТЕРЫ ===")
for j in clusters:
    print(f"P{j+1} =", [i+1 for i in clusters[j]])


# ============================================================
# 📈 ОБЩАЯ (ГЛОБАЛЬНАЯ) ЛИНЕЙНАЯ РЕГРЕССИЯ (sklearn)
# ============================================================
X = np.array(x).reshape(-1, 1)
Y = np.array(y)

lr = LinearRegression().fit(X, Y)

a0_all = lr.intercept_
a1_all = lr.coef_[0]

print("\n=== ОБЩАЯ ФУНКЦИЯ ===")
print(f"y = {a0_all:.2f} + {a1_all:.2f}x")

# ============================================================
# 📌 УРАВНЕНИЯ КЛАСТЕРНЫХ РЕГРЕССИЙ
# ============================================================
print("\n=== КЛАСТЕРНЫЕ РЕГРЕССИИ ===")

for j in range(r):
    a0 = value(model.a0[j])
    a1 = value(model.a1[j])

    print(
        f"Кластер {j+1}: "
        f"y = {a0:.2f} + {a1:.2f}x"
    )


# ============================================================
# 📌 ПОТОЧЕЧНЫЕ ОШИБКИ И СРЕДНЯЯ ПРОЦЕНТНАЯ ОШИБКА
# E = 100 * sum|e_k| / sum(y_k)
# ============================================================
errors = []

for k in range(n):
    ek = value(model.u[k])
    errors.append(ek)

sum_u = sum(errors)
sum_y = sum(y)

E = 100 * sum_u / sum_y

print("\n=== ПОТОЧЕЧНЫЕ ОШИБКИ ===")
for k,e in enumerate(errors, start=1):
    print(f"{k}: {e:.2f}")

print("\n=== СРЕДНЯЯ ПРОЦЕНТНАЯ ОШИБКА ===")
print(f"E = {E:.4f}%")


# ============================================================
# 🎨 МЯГКАЯ ПАЛИТРА (БОЛЕЕ СВЕТЛАЯ И НЕ КОНТРАСТНАЯ)
# ============================================================
def palette(n):
    out = []
    for i in range(n):
        h = (i * 0.618) % 1
        r_, g_, b_ = colorsys.hls_to_rgb(h, 0.6, 0.65)   # светлее фон

        out.append({
            # точки — самые мягкие
            "point": f"rgb({int(r_*255)},{int(g_*255)},{int(b_*255)})",

            # кресты — чуть темнее точек
            "cross": f"rgb({int(r_*210)},{int(g_*210)},{int(b_*210)})",

            # линии — ещё светлее, но читаемые
            "line": f"rgb({int(r_*160)},{int(g_*160)},{int(b_*160)})"
        })
    return out


# ============================================================
# 📊 ПОСТРОЕНИЕ ГРАФИКА
# ============================================================
colors = palette(r)

fig = go.Figure()


# ------------------------------------------------------------
# 1. РЕАЛЬНЫЕ ТОЧКИ (данные)
# ------------------------------------------------------------
for j in range(r):
    xs = [x[i] for i in clusters[j]]
    ys = [y[i] for i in clusters[j]]

    fig.add_trace(go.Scatter(
        x=xs,
        y=ys,
        mode="markers",
        name=f"Кластер {j+1} (факт)",
        marker=dict(size=8, color=colors[j]["point"])
    ))


# ------------------------------------------------------------
# 2. ПРЕДСКАЗАНИЯ МОДЕЛИ (кресты)
# ------------------------------------------------------------
for j in range(r):
    a0 = value(model.a0[j])
    a1 = value(model.a1[j])

    xs = [x[i] for i in clusters[j]]
    ys = [a0 + a1*x[i] for i in clusters[j]]

    fig.add_trace(go.Scatter(
        x=xs,
        y=ys,
        mode="markers",
        name=f"Кластер {j+1} (модель)",
        marker=dict(symbol="x", size=10, color=colors[j]["cross"])
    ))


# ------------------------------------------------------------
# 3. ЛИНЕЙНЫЕ МОДЕЛИ КЛАСТЕРОВ
# ------------------------------------------------------------
x_line = np.linspace(min(x), max(x), 300)

for j in range(r):
    a0 = value(model.a0[j])
    a1 = value(model.a1[j])

    fig.add_trace(go.Scatter(
        x=x_line,
        y=a0 + a1*x_line,
        mode="lines",
        name=f"Регрессия кластер {j+1}",
        line=dict(color=colors[j]["line"], dash="dash")
    ))


# ------------------------------------------------------------
# 4. ОБЩАЯ ЛИНЕЙНАЯ МОДЕЛЬ (по всем данным)
# ------------------------------------------------------------
fig.add_trace(go.Scatter(
    x=x_line,
    y=a0_all + a1_all*x_line,
    mode="lines",
    name="Общая регрессия",
    line=dict(color="rgb(80,80,80)", width=2)
))


# ============================================================
# 🎨 ОФОРМЛЕНИЕ ГРАФИКА
# ============================================================
fig.update_layout(
    title="Кластерная линейная регрессия (MILP)",
    xaxis_title="Инвестиции (x)",
    yaxis_title="Выпуск продукции (y)",
    template="plotly_white",
    legend=dict(title="Обозначения")
)

fig.update_xaxes(showgrid=True, gridcolor="LightGray")
fig.update_yaxes(showgrid=True, gridcolor="LightGray")


# ============================================================
# 🖱 ИНТЕРАКТИВ (ZOOM колесом)
# ============================================================
fig.show(config={
    "scrollZoom": True,
    "displayModeBar": True
})

# ============================================================
# 📉 ГРАФИК ОШИБОК И ФАКТ VS РАСЧЕТ
# ============================================================

fig2 = go.Figure()

# ------------------------------------------------------------
# собираем все точки
# ------------------------------------------------------------
all_points = []

for j in range(r):

    a0 = value(model.a0[j])
    a1 = value(model.a1[j])

    for i in clusters[j]:
        all_points.append({
            "x": x[i],
            "y_fact": y[i],
            "y_calc": a0 + a1*x[i],
            "cluster": j
        })

# сортировка по x
all_points = sorted(all_points, key=lambda p: p["x"])

x_all = [p["x"] for p in all_points]
y_fact_all = [p["y_fact"] for p in all_points]
y_calc_all = [p["y_calc"] for p in all_points]


# ------------------------------------------------------------
# 1 ОБЩАЯ ЛОМАНАЯ ПО ФАКТИЧЕСКИМ
# ------------------------------------------------------------
fig2.add_trace(go.Scatter(
    x=x_all,
    y=y_fact_all,
    mode="lines",
    name="Фактические значения",
    line=dict(
        color="black",
        width=2
    )
))


# ------------------------------------------------------------
# 2 ОБЩАЯ ЛОМАНАЯ ПО РАСЧЕТНЫМ
# ------------------------------------------------------------
fig2.add_trace(go.Scatter(
    x=x_all,
    y=y_calc_all,
    mode="lines",
    name="Расчетные значения",
    line=dict(
        color="gray",
        dash="dot",
        width=2
    )
))


# ------------------------------------------------------------
# 3 ЦВЕТНЫЕ ФАКТИЧЕСКИЕ ТОЧКИ ПО КЛАСТЕРАМ
# ------------------------------------------------------------
for j in range(r):

    xs = [x[i] for i in clusters[j]]
    ys = [y[i] for i in clusters[j]]

    fig2.add_trace(go.Scatter(
        x=xs,
        y=ys,
        mode="markers",
        name=f"Кластер {j+1} факт",
        marker=dict(
            size=9,
            color=colors[j]["point"]
        )
    ))


# ------------------------------------------------------------
# 4 ЦВЕТНЫЕ РАСЧЕТНЫЕ КРЕСТЫ ПО КЛАСТЕРАМ
# ------------------------------------------------------------
for j in range(r):

    a0 = value(model.a0[j])
    a1 = value(model.a1[j])

    xs = [x[i] for i in clusters[j]]
    ys = [a0 + a1*x[i] for i in clusters[j]]

    fig2.add_trace(go.Scatter(
        x=xs,
        y=ys,
        mode="markers",
        name=f"Кластер {j+1} расчет",
        marker=dict(
            symbol="x",
            size=10,
            color=colors[j]["cross"]
        )
    ))


# ------------------------------------------------------------
# 5 ВЕРТИКАЛЬНЫЕ ОШИБКИ
# ------------------------------------------------------------
for p in all_points:

    j = p["cluster"]

    fig2.add_trace(go.Scatter(
        x=[p["x"], p["x"]],
        y=[p["y_fact"], p["y_calc"]],
        mode="lines",
        showlegend=False,
        line=dict(
            color=colors[j]["line"],
            width=1.5
        )
    ))


# ============================================================
# ОФОРМЛЕНИЕ
# ============================================================
fig2.update_layout(
    title="Фактические и расчетные значения с ошибками",
    xaxis_title="Инвестиции (x)",
    yaxis_title="Выпуск продукции (y)",
    template="plotly_white"
)

fig2.update_xaxes(showgrid=True, gridcolor="LightGray")
fig2.update_yaxes(showgrid=True, gridcolor="LightGray")

fig2.show(config={
    "scrollZoom":True,
    "displayModeBar":True
})