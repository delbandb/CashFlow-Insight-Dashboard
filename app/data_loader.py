from __future__ import annotations

from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_data() -> dict[str, pd.DataFrame]:
    clients = pd.read_csv(DATA_DIR / "clients.csv", parse_dates=["start_date"])
    invoices = pd.read_csv(DATA_DIR / "invoices.csv", parse_dates=["issue_date", "due_date"])
    payments = pd.read_csv(DATA_DIR / "payments.csv", parse_dates=["payment_date"])
    expenses = pd.read_csv(DATA_DIR / "expenses.csv", parse_dates=["expense_date"])
    return {
        "clients": clients,
        "invoices": invoices,
        "payments": payments,
        "expenses": expenses,
    }
