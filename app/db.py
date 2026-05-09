from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd

from app.data_loader import load_data


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_DIR = Path(tempfile.gettempdir()) / "CashFlowInsightDashboard"
DB_DIR = Path(os.environ.get("CFI_DB_DIR", DEFAULT_DB_DIR))
DB_PATH = DB_DIR / "cashflow_insight.db"


def get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def seed_database() -> Path:
    data = load_data()
    connection = get_connection()
    try:
        schema_path = BASE_DIR / "sql" / "schema.sql"
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        table_order = ["clients", "invoices", "payments", "expenses"]
        for table_name in table_order:
            data[table_name].to_sql(table_name, connection, if_exists="append", index=False)
        connection.commit()
    finally:
        connection.close()
    return DB_PATH


def read_sql_frame(query: str, params: tuple | list | None = None) -> pd.DataFrame:
    connection = get_connection()
    try:
        return pd.read_sql_query(query, connection, params=params)
    finally:
        connection.close()
