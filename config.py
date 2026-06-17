"""Application-wide configuration constants."""

from pathlib import Path

SOLVER_NAME = "appsi_highs"
COEF_BOUND = 1e6
BIG_M_MIN = 1.0

# ── Local embedded storage ──────────────────────────────────────────────────
# A single SQLite file shipped with the program keeps imported datasets,
# computed results and exported PDF reports.
BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
DB_PATH = STORAGE_DIR / "milp.duckdb"
