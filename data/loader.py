"""Excel loading utilities — supports .xlsx and .xls files."""

from pathlib import Path

import pandas as pd


def load_excel(path: str | Path) -> pd.DataFrame:
    """Load an Excel file and return the full numeric DataFrame.

    All non-numeric columns are silently dropped.  The caller is responsible
    for choosing which columns to use as X (predictors) and Y (target).
    """
    excel_path = Path(path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Файл не найден: {excel_path}")

    suffix = excel_path.suffix.lower()
    if suffix not in (".xlsx", ".xls", ".xlsm", ".xlsb", ".ods"):
        raise ValueError(
            f"Неподдерживаемый формат файла: {suffix}\n"
            "Поддерживаются: .xlsx, .xls, .xlsm, .xlsb, .ods"
        )

    try:
        df = pd.read_excel(excel_path, sheet_name=0)
    except Exception as exc:
        raise ValueError(f"Ошибка чтения файла Excel: {exc}") from exc

    if df.empty:
        raise ValueError("Файл не должен быть пустым")

    # Keep only numeric columns
    df_num = df.select_dtypes(include="number")
    if df_num.shape[1] < 2:
        raise ValueError(
            "Файл должен содержать минимум 2 числовых столбца (X и Y)"
        )

    if df_num.isna().any().any():
        df_num = df_num.dropna()
        if df_num.empty:
            raise ValueError("После удаления строк с пропусками набор данных пуст")

    return df_num.reset_index(drop=True)