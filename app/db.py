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
    DB_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def seed_database() -> Path:
    data = load_data()
    connection = get_connection()
    try:
        schema_path = BASE_DIR / "sql" / "schema.sql"
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        for table_name, frame in data.items():
            frame.to_sql(table_name, connection, if_exists="replace", index=False)
        connection.commit()
    finally:
        connection.close()
    return DB_PATH


def read_sql_frame(query: str) -> pd.DataFrame:
    connection = get_connection()
    try:
        return pd.read_sql_query(query, connection)
    finally:
        connection.close()
