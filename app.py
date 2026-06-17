"""GUI entry point for the MILP cluster regression application."""

import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

import qt_material

from gui.main_window import MainWindow
from gui.styles import CUSTOM_CSS, get_extra


def _ensure_standard_streams() -> None:
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def main() -> int:
    _ensure_standard_streams()
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("MILP Cluster Analysis")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Diplom")

    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferDefaultHinting)
    app.setFont(font)

    # ── Apply qt-material base theme ──────────────────────────────────────────
    qt_material.apply_stylesheet(
        app,
        theme="dark_purple.xml",
        extra=get_extra(),
        invert_secondary=False,
    )

    # ── Layer our custom overrides on top ─────────────────────────────────────
    app.setStyleSheet(app.styleSheet() + CUSTOM_CSS)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())