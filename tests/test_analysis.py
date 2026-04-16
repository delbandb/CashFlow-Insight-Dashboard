from pathlib import Path

from app.analysis import build_metrics
from app.build_database import seed_database
from app.db import read_sql_frame
from app.sql_queries import SUMMARY_QUERY


def test_summary_metrics_are_consistent():
    metrics = build_metrics()
    summary = metrics["summary"]

    assert summary["paid_income"] == 45700.0
    assert summary["invoiced_income"] == 57450.0
    assert summary["total_expenses"] == 32200.0
    assert summary["net_cash_flow"] == 13500.0
    assert summary["active_clients"] == 6
    assert summary["overdue_invoice_count"] == 2


def test_monthly_cash_flow_has_expected_columns():
    metrics = build_metrics()
    monthly_cash_flow = metrics["monthly_cash_flow"]

    assert list(monthly_cash_flow.columns) == ["month", "income", "expenses", "net_cash_flow"]
    assert len(monthly_cash_flow) == 4


def test_top_client_is_identified():
    metrics = build_metrics()
    top_client = metrics["revenue_by_client"].iloc[0]

    assert top_client["client_name"] == "Solara Retail"
    assert top_client["invoice_amount"] == 16150


def test_sqlite_database_is_built_and_queryable():
    db_path = seed_database()
    summary_frame = read_sql_frame(SUMMARY_QUERY)

    assert Path(db_path).exists()
    assert len(summary_frame) == 1
    assert float(summary_frame.iloc[0]["paid_income"]) == 45700.0
