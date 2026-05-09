from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

from app.db import seed_database
from app.data_loader import load_data
from app.sql_queries import (
    get_avg_payment_delay_by_client,
    get_collections_gap,
    get_expense_by_category,
    get_monthly_cashflow,
    get_overdue_invoices,
    get_top_clients_by_revenue,
)


def calculate_kpis(
    invoices_df: pd.DataFrame,
    payments_df: pd.DataFrame,
    expenses_df: pd.DataFrame,
) -> dict[str, float]:
    total_revenue = float(invoices_df["invoice_amount"].sum())
    total_collected = float(payments_df["payment_amount"].sum())
    total_expenses = float(expenses_df["amount"].sum())
    collections_gap = total_revenue - total_collected
    net_cash_flow = total_collected - total_expenses
    return {
        "total_revenue_invoiced": round(total_revenue, 2),
        "total_cash_collected": round(total_collected, 2),
        "collections_gap": round(collections_gap, 2),
        "net_cash_flow": round(net_cash_flow, 2),
    }


def flag_overdue_invoices(
    invoices_df: pd.DataFrame,
    as_of_date: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    reference_date = pd.Timestamp(as_of_date or pd.Timestamp.today().normalize())
    flagged = invoices_df.copy()
    flagged["due_date"] = pd.to_datetime(flagged["due_date"])
    flagged["status"] = flagged["status"].fillna("pending").str.lower()
    flagged["days_overdue"] = np.where(
        flagged["due_date"] < reference_date,
        (reference_date - flagged["due_date"]).dt.days,
        0,
    )
    return flagged[
        (flagged["status"] == "overdue")
        | ((flagged["status"] != "paid") & (flagged["due_date"] < reference_date))
    ].copy()


def summarize_expenses_by_category(expenses_df: pd.DataFrame) -> pd.DataFrame:
    return (
        expenses_df.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values(["amount", "category"], ascending=[False, True])
        .reset_index(drop=True)
    )


def forecast_cash_flow(df: pd.DataFrame, months_ahead: int = 3) -> pd.DataFrame:
    monthly = df.copy()
    if "month" not in monthly.columns or "net_cash_flow" not in monthly.columns:
        raise ValueError("DataFrame must contain 'month' and 'net_cash_flow' columns.")

    monthly["month"] = pd.to_datetime(monthly["month"])
    monthly = monthly.sort_values("month").reset_index(drop=True)
    monthly["period_index"] = np.arange(len(monthly))

    x = monthly["period_index"].to_numpy(dtype=float)
    y = monthly["net_cash_flow"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, 1)

    historical_fit = (slope * x) + intercept
    residuals = y - historical_fit
    band_size = float(np.std(residuals) * 0.15)

    forecast_index = np.arange(len(monthly), len(monthly) + months_ahead, dtype=float)
    forecast_values = (slope * forecast_index) + intercept
    start_month = monthly["month"].iloc[-1] + pd.offsets.MonthBegin(1)
    forecast_months = pd.date_range(start=start_month, periods=months_ahead, freq="MS")

    return pd.DataFrame(
        {
            "month": forecast_months,
            "forecast_net_cash_flow": forecast_values,
            "lower_confidence": forecast_values - band_size,
            "upper_confidence": forecast_values + band_size,
        }
    )


def build_metrics() -> dict[str, object]:
    seed_database()
    data = load_data()

    invoices = data["invoices"].copy()
    payments = data["payments"].copy()
    expenses = data["expenses"].copy()
    clients = data["clients"].copy()

    monthly_cashflow = get_monthly_cashflow()
    top_clients = get_top_clients_by_revenue()
    overdue_invoices = get_overdue_invoices()
    expense_by_category = get_expense_by_category()
    avg_delay_by_client = get_avg_payment_delay_by_client()
    collections_gap = get_collections_gap()

    kpis = calculate_kpis(invoices, payments, expenses)
    summary = collections_gap.iloc[0].to_dict()
    summary.update(kpis)
    summary["number_of_overdue_invoices"] = int(len(overdue_invoices))
    summary["average_payment_delay_days"] = round(
        float(avg_delay_by_client["avg_payment_delay_days"].mean()) if not avg_delay_by_client.empty else 0.0,
        2,
    )

    invoice_tracker = (
        invoices.merge(clients[["client_id", "client_name"]], on="client_id", how="left")
        .assign(
            due_date=lambda frame: pd.to_datetime(frame["due_date"]),
            issue_date=lambda frame: pd.to_datetime(frame["issue_date"]),
        )
        .sort_values(["due_date", "invoice_id"])
        .reset_index(drop=True)
    )
    reference_date = pd.Timestamp(datetime(2024, 12, 31))
    invoice_tracker["days_overdue"] = np.where(
        invoice_tracker["due_date"] < reference_date,
        (reference_date - invoice_tracker["due_date"]).dt.days,
        0,
    )

    return {
        "summary": summary,
        "raw": data,
        "monthly_cashflow": monthly_cashflow,
        "top_clients": top_clients,
        "overdue_invoices": overdue_invoices,
        "expense_by_category": expense_by_category,
        "avg_delay_by_client": avg_delay_by_client,
        "invoice_tracker": invoice_tracker,
    }
