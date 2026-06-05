"""CSV loading utilities."""

from pathlib import Path
from typing import Sequence

import pandas as pd

REQUIRED_COLUMNS: Sequence[str] = ("x", "y")


def load_csv(path: str | Path) -> tuple[list[float], list[float]]:
    """Load a two-column dataset from CSV.

    The optimisation model expects numeric ``x`` and ``y`` columns without
    missing values.  Validation is done here so the CLI and GUI fail with the
    same clear message.
    """
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV файл не найден: {csv_path}")

    df = pd.read_csv(csv_path)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError("CSV должен содержать столбцы: x, y")

    data = df.loc[:, list(REQUIRED_COLUMNS)].copy()
    for column in REQUIRED_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    if data.empty:
        raise ValueError("CSV не должен быть пустым")
    if data.isna().any().any():
        raise ValueError("Столбцы x и y должны содержать только числовые значения")

    return data["x"].tolist(), data["y"].tolist()