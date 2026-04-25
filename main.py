from data.loader import load_csv
from model.build_model import build_model
from solver.solve_model import solve_model
from analysis.extract_results import extract_results
from analysis.metrics import mean_percent_error
from analysis.validation import validate_solution
from visualization.plot_clusters import plot_clusters


# -----------------------------
# ВВОД ЧИСЕЛ
# -----------------------------
def ask_int(text, allow_empty=False):

    while True:
        s = input(text).strip()

        if allow_empty and s == "":
            return None

        try:
            return int(s)
        except:
            print("Введите целое число")


def get_cluster_sizes(n, r):

    print("\nРежим задания размеров кластеров:")
    print("0 - не задавать")
    print("1 - частично задать (любые кластеры)")
    print("2 - равные кластеры")

    mode = ask_int("Выбор режима: ")


    # -----------------------------------
    # 0. полностью свободно
    # -----------------------------------
    if mode == 0:
        return None


    # -----------------------------------
    # 1. частично задаём
    # -----------------------------------
    if mode == 1:

        sizes = [None] * r
        fixed_sum = 0

        print("\nВводи размеры кластеров (Enter = пропустить)")

        for j in range(r - 1):

            val = input(f"|P{j+1}| = ").strip()

            if val == "":
                continue

            sizes[j] = int(val)
            fixed_sum += sizes[j]


        sizes[r - 1] = n - fixed_sum

        if sizes[r - 1] <= 0:
            raise ValueError("Некорректное разбиение: последний кластер <= 0")

        return sizes


    # -----------------------------------
    # 2. равномерно
    # -----------------------------------
    if mode == 2:

        base = n // r

        sizes = [base] * r
        sizes[-1] = n - base * (r - 1)

        return sizes


    return None

# -----------------------------
# MAIN
# -----------------------------
def main():

    print("\nКластерная линейная регрессия (MILP)")

    # -------------------------
    # файл данных
    # -------------------------
    file_path = input(
        "CSV файл [Enter=data/sample_data.csv]: "
    ).strip()

    if not file_path:
        file_path = "data/sample_data.csv"


    # -------------------------
    # число кластеров
    # -------------------------
    r = ask_int("Число кластеров r: ")


    # -------------------------
    # загружаем данные
    # -------------------------
    x, y = load_csv(file_path)
    n = len(x)


    # -------------------------
    # режим кластеров
    # -------------------------
    cluster_sizes = get_cluster_sizes(n, r)


    # -------------------------
    # строим модель
    # -------------------------
    print("\nСтроим MILP модель...")

    model = build_model(
        x,
        y,
        r,
        cluster_sizes
    )


    # -------------------------
    # решаем MILP
    # -------------------------
    print("Решаем...")

    solve_model(model)


    # -------------------------
    # извлекаем результат
    # -------------------------
    results = extract_results(
        model,
        x,
        y,
        r
    )


    # -------------------------
    # вывод кластеров
    # -------------------------
    print("\n=== КЛАСТЕРЫ ===")

    for j, pts in results["clusters"].items():
        print(
            f"P{j + 1} =",
            [k + 1 for k in pts]
        )


    # -------------------------
    # регрессии
    # -------------------------
    print("\n=== МОДЕЛИ ===")

    for j, (a0, a1) in enumerate(results["coeffs"]):

        print(
            f"Кластер {j + 1}: "
            f"y = {a0:.2f} + {a1:.2f}x"
        )


    # -------------------------
    # ошибка
    # -------------------------
    E = mean_percent_error(
        y,
        results["u"]
    )

    print(f"\nE = {E:.4f}%")


    # -------------------------
    # проверка
    # -------------------------
    validate_solution(
        results,
        x,
        y
    )


    # -------------------------
    # график
    # -------------------------
    plot_clusters(
        results,
        x,
        y
    )


# -----------------------------
if __name__ == "__main__":
    main()