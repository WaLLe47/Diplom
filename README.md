# MILP Cluster Analysis

Приложение для кластерной линейной регрессии на основе **MILP** (Mixed Integer Linear Programming).

## Структура проекта

```
├── app.py                  # Точка входа (запуск Qt-приложения)
├── config.py               # Глобальные константы (солвер, границы)
├── requirements.txt        # Зависимости
│
├── data/
│   ├── loader.py           # Загрузка и валидация CSV
│   └── sample_data*.csv    # Примеры данных
│
├── model/
│   ├── build_model.py      # Сборка Pyomo-модели
│   ├── variables.py        # Переменные MILP
│   ├── objective.py        # Целевая функция
│   └── constraints.py      # Ограничения
│
├── solver/
│   └── solve_model.py      # Запуск HiGHS решателя
│
├── analysis/
│   ├── extract_results.py  # Извлечение результатов из модели
│   ├── metrics.py          # Средняя ошибка (E)
│   └── validation.py       # Проверка корректности решения
│
├── visualization/
│   └── plot_clusters.py    # Plotly-графики кластеров и ошибок
│
└── gui/
    ├── main_window.py      # Главное окно приложения
    ├── burger_menu.py      # Боковое меню с анимацией
    ├── loading_overlay.py  # Оверлей загрузки со спиннером
    ├── dialogs.py          # Диалог предпросмотра данных
    ├── pdf_export.py       # Экспорт отчёта в PDF
    ├── styles.py           # Темы (dark / light) и CSS
    └── worker.py           # Фоновый поток для решателя
```

## Установка

```bash
pip install -r requirements.txt
```

## Запуск

```bash
python app.py
```

## Использование

1. **Загрузить CSV** — файл с двумя столбцами `x` и `y`
2. **Настроить параметры** — число кластеров, режим разбиения
3. **Запустить расчёт** — MILP строит оптимальную кластерную регрессию
4. **Экспортировать PDF** — отчёт с уравнениями и графиками

## Формат CSV

```csv
x,y
1.0,2.3
2.5,4.1
...
```
