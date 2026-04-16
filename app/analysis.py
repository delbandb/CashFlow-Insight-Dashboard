from __future__ import annotations

import pandas as pd

from app.db import read_sql_frame, seed_database
from app.data_loader import load_data
from app.sql_queries import (
    EXPENSE_CATEGORY_QUERY,
    LATE_PAYMENT_QUERY,
    MONTHLY_CASH_FLOW_QUERY,
    OVERDUE_INVOICES_QUERY,
    SUMMARY_QUERY,
    TOP_CLIENTS_QUERY,
)


def build_metrics() -> dict[str, object]:
    seed_database()

    summary_frame = read_sql_frame(SUMMARY_QUERY)
    monthly_cash_flow = read_sql_frame(MONTHLY_CASH_FLOW_QUERY)
    revenue_by_client = read_sql_frame(TOP_CLIENTS_QUERY)
    late_payment_summary = read_sql_frame(LATE_PAYMENT_QUERY)
    expense_by_category = read_sql_frame(EXPENSE_CATEGORY_QUERY)
    overdue_invoices = read_sql_frame(OVERDUE_INVOICES_QUERY)

    monthly_cash_flow["month"] = pd.to_datetime(monthly_cash_flow["month"])

    dashboard_table = monthly_cash_flow.copy()
    dashboard_table["month"] = dashboard_table["month"].dt.strftime("%Y-%m")
    dashboard_table[["income", "expenses", "net_cash_flow"]] = dashboard_table[
        ["income", "expenses", "net_cash_flow"]
    ].round(2)

    summary_row = summary_frame.iloc[0]

    return {
        "summary": {
            "paid_income": round(float(summary_row["paid_income"]), 2),
            "invoiced_income": round(float(summary_row["invoiced_income"]), 2),
            "total_expenses": round(float(summary_row["total_expenses"]), 2),
            "net_cash_flow": round(float(summary_row["net_cash_flow"]), 2),
            "active_clients": int(summary_row["active_clients"]),
            "overdue_invoice_count": int(summary_row["overdue_invoice_count"]),
        },
        "revenue_by_client": revenue_by_client,
        "late_payment_summary": late_payment_summary,
        "monthly_cash_flow": monthly_cash_flow,
        "expense_by_category": expense_by_category,
        "dashboard_table": dashboard_table,
        "overdue_invoices": overdue_invoices,
    }
