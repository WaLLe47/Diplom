"""GUI entry point for the MILP cluster regression application."""

import os
import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow


def _ensure_standard_streams() -> None:
    """Provide dummy streams for frozen GUI builds without stdout/stderr."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def main() -> int:
    """Start the Qt application."""
    _ensure_standard_streams()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())