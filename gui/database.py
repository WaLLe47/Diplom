"""Local embedded DuckDB storage for datasets, results and PDF reports.

The whole history lives in a single file (``config.DB_PATH``) that ships with
the program, so imported data, computed models and exported PDF reports are
persisted between runs without any external database server.

DuckDB has no ``AUTOINCREMENT``; surrogate keys come from sequences, and the
inserted id is read back with ``INSERT ... RETURNING id``. Query helpers return
plain ``dict`` rows so callers stay independent of the driver.
"""

from __future__ import annotations

import json
from datetime import datetime
from io import StringIO
from typing import Any

import duckdb
import pandas as pd

from config import DB_PATH, STORAGE_DIR

_SCHEMA = (
    "CREATE SEQUENCE IF NOT EXISTS seq_datasets START 1",
    "CREATE SEQUENCE IF NOT EXISTS seq_results START 1",
    "CREATE SEQUENCE IF NOT EXISTS seq_reports START 1",
    """
    CREATE TABLE IF NOT EXISTS datasets (
        id          INTEGER PRIMARY KEY DEFAULT nextval('seq_datasets'),
        name        VARCHAR NOT NULL,
        imported_at VARCHAR NOT NULL,
        n_rows      INTEGER NOT NULL,
        n_cols      INTEGER NOT NULL,
        columns     VARCHAR NOT NULL,   -- JSON list of column names
        data_csv    VARCHAR NOT NULL    -- full numeric table as CSV text
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS results (
        id            INTEGER PRIMARY KEY DEFAULT nextval('seq_results'),
        dataset_id    INTEGER,
        created_at    VARCHAR NOT NULL,
        n_clusters    INTEGER NOT NULL,
        x_cols        VARCHAR NOT NULL,  -- JSON list
        y_col         VARCHAR NOT NULL,
        error_e       DOUBLE  NOT NULL,
        global_coeffs VARCHAR NOT NULL,  -- JSON [intercept, slope]
        coeffs        VARCHAR NOT NULL,  -- JSON [[a0, [a1..]], ...]
        clusters      VARCHAR NOT NULL   -- JSON {cluster_idx: [point_idx, ...]}
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reports (
        id         INTEGER PRIMARY KEY DEFAULT nextval('seq_reports'),
        result_id  INTEGER,
        created_at VARCHAR NOT NULL,
        file_name  VARCHAR NOT NULL,
        pdf        BLOB    NOT NULL
    )
    """,
)


class Database:
    """Thin wrapper around a local DuckDB database."""

    def __init__(self, path=DB_PATH) -> None:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect(str(path))
        for statement in _SCHEMA:
            self._conn.execute(statement)

    # ── internal helpers ──────────────────────────────────────────────────────

    def _query(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        cur = self._conn.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def _insert_returning_id(self, sql: str, params: tuple) -> int:
        row = self._conn.execute(sql, params).fetchone()
        return int(row[0])

    # ── writes ──────────────────────────────────────────────────────────────

    def save_dataset(self, name: str, df: pd.DataFrame) -> int:
        return self._insert_returning_id(
            "INSERT INTO datasets (name, imported_at, n_rows, n_cols, columns, data_csv)"
            " VALUES (?, ?, ?, ?, ?, ?) RETURNING id",
            (
                name,
                datetime.now().isoformat(timespec="seconds"),
                len(df),
                df.shape[1],
                json.dumps(list(df.columns)),
                df.to_csv(index=False),
            ),
        )

    def save_result(
        self,
        dataset_id: int | None,
        n_clusters: int,
        x_cols: list[str],
        y_col: str,
        error_e: float,
        global_coeffs: tuple[float, float],
        coeffs: list[tuple[float, list[float]]],
        clusters: dict[int, list[int]],
    ) -> int:
        return self._insert_returning_id(
            "INSERT INTO results (dataset_id, created_at, n_clusters, x_cols, y_col,"
            " error_e, global_coeffs, coeffs, clusters)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
            (
                dataset_id,
                datetime.now().isoformat(timespec="seconds"),
                n_clusters,
                json.dumps(x_cols, ensure_ascii=False),
                y_col,
                float(error_e),
                json.dumps(list(global_coeffs)),
                json.dumps([[a0, list(a1)] for a0, a1 in coeffs]),
                json.dumps({str(k): list(v) for k, v in clusters.items()}),
            ),
        )

    def save_report(
        self, result_id: int | None, file_name: str, pdf_bytes: bytes
    ) -> int:
        return self._insert_returning_id(
            "INSERT INTO reports (result_id, created_at, file_name, pdf)"
            " VALUES (?, ?, ?, ?) RETURNING id",
            (
                result_id,
                datetime.now().isoformat(timespec="seconds"),
                file_name,
                pdf_bytes,
            ),
        )

    # ── reads ───────────────────────────────────────────────────────────────

    def list_datasets(self) -> list[dict[str, Any]]:
        return self._query(
            "SELECT id, name, imported_at, n_rows, n_cols FROM datasets"
            " ORDER BY id DESC"
        )

    def list_results(self) -> list[dict[str, Any]]:
        return self._query(
            "SELECT r.id, r.created_at, r.n_clusters, r.x_cols, r.y_col, r.error_e,"
            " d.name AS dataset_name"
            " FROM results r LEFT JOIN datasets d ON d.id = r.dataset_id"
            " ORDER BY r.id DESC"
        )

    def list_reports(self) -> list[dict[str, Any]]:
        return self._query(
            "SELECT id, result_id, created_at, file_name,"
            " octet_length(pdf) AS size_bytes FROM reports ORDER BY id DESC"
        )

    def get_dataset_df(self, dataset_id: int) -> pd.DataFrame:
        rows = self._query(
            "SELECT data_csv FROM datasets WHERE id = ?", (dataset_id,)
        )
        if not rows:
            raise KeyError(f"Набор данных #{dataset_id} не найден")
        return pd.read_csv(StringIO(rows[0]["data_csv"]))

    def get_report_pdf(self, report_id: int) -> tuple[str, bytes]:
        rows = self._query(
            "SELECT file_name, pdf FROM reports WHERE id = ?", (report_id,)
        )
        if not rows:
            raise KeyError(f"Отчёт #{report_id} не найден")
        return rows[0]["file_name"], bytes(rows[0]["pdf"])

    # ── deletes ───────────────────────────────────────────────────────────────

    def delete(self, table: str, row_id: int) -> None:
        if table not in {"datasets", "results", "reports"}:
            raise ValueError(f"Неизвестная таблица: {table}")
        self._conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))

    def close(self) -> None:
        self._conn.close()


_db: Database | None = None


def get_db() -> Database:
    """Return a lazily-created process-wide :class:`Database` instance."""
    global _db
    if _db is None:
        _db = Database()
    return _db
