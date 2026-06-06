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
        x: list[float],
        y: list[float],
        r: int,
        cluster_sizes: list[int | None] | None,
    ) -> None:
        super().__init__()
        self.x = x
        self.y = y
        self.r = r
        self.cluster_sizes = cluster_sizes

    def run(self) -> None:
        try:
            model = build_model(self.x, self.y, self.r, self.cluster_sizes)
            solve_model(model)
            results = extract_results(model, self.x, self.y, self.r)
            slope, intercept = np.polyfit(np.asarray(self.x), np.asarray(self.y), 1)
            self.finished.emit(results, (float(intercept), float(slope)))
        except Exception as exc:
            self.error.emit(str(exc))
