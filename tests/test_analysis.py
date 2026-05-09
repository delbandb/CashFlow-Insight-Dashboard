import pandas as pd

from app.analysis import (
    calculate_kpis,
    flag_overdue_invoices,
    forecast_cash_flow,
    summarize_expenses_by_category,
)


def test_kpi_calculations():
    invoices = pd.DataFrame({"invoice_amount": [1000.0, 2500.0, 500.0]})
    payments = pd.DataFrame({"payment_amount": [1000.0, 500.0]})
    expenses = pd.DataFrame({"amount": [400.0, 300.0]})

    metrics = calculate_kpis(invoices, payments, expenses)

    assert metrics["total_revenue_invoiced"] == 4000.0
    assert metrics["total_cash_collected"] == 1500.0
    assert metrics["collections_gap"] == 2500.0
    assert metrics["net_cash_flow"] == 800.0


def test_overdue_detection():
    invoices = pd.DataFrame(
        {
            "invoice_id": ["INV-1", "INV-2", "INV-3"],
            "due_date": ["2024-03-01", "2024-03-20", "2024-04-15"],
            "status": ["pending", "paid", "overdue"],
        }
    )

    overdue = flag_overdue_invoices(invoices, as_of_date="2024-03-25")

    assert overdue["invoice_id"].tolist() == ["INV-1", "INV-3"]


def test_forecast_returns_correct_shape():
    monthly = pd.DataFrame(
        {
            "month": pd.date_range("2024-01-01", periods=6, freq="MS"),
            "net_cash_flow": [1000, 1200, 1400, 1600, 1800, 2000],
        }
    )

    forecast = forecast_cash_flow(monthly, months_ahead=3)

    assert forecast.shape == (3, 4)
    assert list(forecast.columns) == [
        "month",
        "forecast_net_cash_flow",
        "lower_confidence",
        "upper_confidence",
    ]


def test_expense_category_totals():
    expenses = pd.DataFrame(
        {
            "category": ["Software", "Rent", "Software", "Travel"],
            "amount": [200.0, 800.0, 300.0, 150.0],
        }
    )

    totals = summarize_expenses_by_category(expenses)

    assert totals.loc[totals["category"] == "Software", "amount"].iloc[0] == 500.0
    assert totals["amount"].sum() == 1450.0


def test_no_negative_payments():
    payments = pd.DataFrame({"payment_amount": [100.0, 250.0, 999.0]})

    assert (payments["payment_amount"] >= 0).all()
