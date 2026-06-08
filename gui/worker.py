"""Background thread for MILP solving."""

from typing import Any

import numpy as np
from PySide6.QtCore import QThread, Signal

from analysis.extract_results import extract_results
from model.build_model import build_model
from solver.solve_model import solve_model


class SolverThread(QThread):
    """Runs the MILP model outside the UI thread to keep the GUI responsive."""

    finished: Signal = Signal(dict, tuple)
    error: Signal = Signal(str)

    def __init__(
        self,
        X: list[list[float]],      # rows=observations, cols=features
        y: list[float],
        r: int,
        cluster_sizes: list[int | None] | None,
        x_cols: list[str],         # feature names for display
        y_col: str,
    ) -> None:
        super().__init__()
        self.X = X
        self.y = y
        self.r = r
        self.cluster_sizes = cluster_sizes
        self.x_cols = x_cols
        self.y_col = y_col

    def run(self) -> None:
        try:
            model = build_model(self.X, self.y, self.r, self.cluster_sizes)
            solve_model(model)
            results = extract_results(model, self.X, self.y, self.r)

            # Global regression (OLS) — use first X column for 2D plot compat
            x0 = [row[0] for row in self.X]
            slope, intercept = np.polyfit(np.asarray(x0), np.asarray(self.y), 1)
            self.finished.emit(results, (float(intercept), float(slope)))
        except Exception as exc:
            self.error.emit(str(exc))