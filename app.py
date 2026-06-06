"""GUI entry point for the MILP cluster regression application."""

import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow


def _ensure_standard_streams() -> None:
    """Provide dummy streams for frozen/GUI builds without stdout/stderr."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")  # noqa: WPS515
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")  # noqa: WPS515


def main() -> int:
    """Configure and start the Qt application."""
    _ensure_standard_streams()

    # High-DPI scaling — must be set before QApplication is created
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("MILP Cluster Analysis")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Diplom")

    # Comfortable default font
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferDefaultHinting)
    app.setFont(font)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
