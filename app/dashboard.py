from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.analysis import build_metrics, forecast_cash_flow


DARK_TEMPLATE = "plotly_dark"
PLOT_BACKGROUND = "#0e1117"
TEXT_COLOR = "#ffffff"
ACCENT = "#1f77b4"
GREEN = "#2ca02c"


def euro(value: float) -> str:
    return f"EUR {value:,.0f}"


def apply_dark_layout(fig: go.Figure, title: str, xaxis_title: str, yaxis_title: str) -> go.Figure:
    fig.update_layout(
        template=DARK_TEMPLATE,
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        paper_bgcolor=PLOT_BACKGROUND,
        plot_bgcolor=PLOT_BACKGROUND,
        font={"color": TEXT_COLOR},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        margin={"l": 40, "r": 20, "t": 70, "b": 40},
    )
    return fig


def prepare_filtered_frames() -> dict[str, pd.DataFrame]:
    metrics = build_metrics()
    raw = metrics["raw"]
    invoices = raw["invoices"].copy()
    payments = raw["payments"].copy()
    expenses = raw["expenses"].copy()
    clients = raw["clients"].copy()

    invoices["issue_date"] = pd.to_datetime(invoices["issue_date"])
    invoices["due_date"] = pd.to_datetime(invoices["due_date"])
    payments["payment_date"] = pd.to_datetime(payments["payment_date"])
    expenses["expense_date"] = pd.to_datetime(expenses["expense_date"])

    invoices = invoices.merge(clients[["client_id", "client_name"]], on="client_id", how="left")
    payments = payments.merge(
        invoices[["invoice_id", "client_id", "client_name", "due_date"]],
        on="invoice_id",
        how="left",
    )

    month_options = list(pd.period_range("2024-01", "2024-12", freq="M").astype(str))
    st.sidebar.title("💰 CashFlow Insight Dashboard")
    selected_range = st.sidebar.select_slider("Month range", options=month_options, value=(month_options[0], month_options[-1]))
    client_options = sorted(clients["client_name"].tolist())
    selected_clients = st.sidebar.multiselect("Client filter", options=client_options, default=client_options)
    st.sidebar.info("All data is synthetically generated for demo purposes")
    st.sidebar.caption("[🔗 View on GitHub](https://github.com/delbandb/CashFlow-Insight-Dashboard)")

    selected_periods = pd.period_range(selected_range[0], selected_range[1], freq="M")
    selected_labels = {str(period) for period in selected_periods}
    invoice_mask = (
        invoices["issue_date"].dt.to_period("M").astype(str).isin(selected_labels)
        & invoices["client_name"].isin(selected_clients)
    )
    payment_mask = (
        payments["payment_date"].dt.to_period("M").astype(str).isin(selected_labels)
        & payments["client_name"].isin(selected_clients)
    )
    expense_mask = expenses["expense_date"].dt.to_period("M").astype(str).isin(selected_labels)

    return {
        "invoices": invoices.loc[invoice_mask].copy(),
        "payments": payments.loc[payment_mask].copy(),
        "expenses": expenses.loc[expense_mask].copy(),
        "selected_periods": selected_periods,
    }


def build_monthly_summary(invoices: pd.DataFrame, payments: pd.DataFrame, expenses: pd.DataFrame, selected_periods: pd.PeriodIndex) -> pd.DataFrame:
    period_frame = pd.DataFrame({"month_period": selected_periods})
    period_frame["month"] = period_frame["month_period"].dt.to_timestamp()
    monthly_invoiced = (
        invoices.assign(month_period=invoices["issue_date"].dt.to_period("M"))
        .groupby("month_period", as_index=False)["invoice_amount"]
        .sum()
        .rename(columns={"invoice_amount": "invoiced"})
    )
    monthly_collected = (
        payments.assign(month_period=payments["payment_date"].dt.to_period("M"))
        .groupby("month_period", as_index=False)["payment_amount"]
        .sum()
        .rename(columns={"payment_amount": "collected"})
    )
    monthly_expenses = (
        expenses.assign(month_period=expenses["expense_date"].dt.to_period("M"))
        .groupby("month_period", as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "expenses"})
    )
    monthly = (
        period_frame.merge(monthly_invoiced, on="month_period", how="left")
        .merge(monthly_collected, on="month_period", how="left")
        .merge(monthly_expenses, on="month_period", how="left")
        .fillna(0)
        .sort_values("month")
    )
    monthly["net_cash_flow"] = monthly["collected"] - monthly["expenses"]
    return monthly


def render_executive_summary(monthly: pd.DataFrame, invoices: pd.DataFrame, payments: pd.DataFrame, expenses: pd.DataFrame) -> None:
    total_invoiced = float(invoices["invoice_amount"].sum())
    total_collected = float(payments["payment_amount"].sum())
    collections_gap = total_invoiced - total_collected
    net_cash_flow = float(total_collected - expenses["amount"].sum())
    overdue_count = int((invoices["status"] == "overdue").sum())
    avg_delay = float((payments["payment_date"] - payments["due_date"]).dt.days.mean()) if not payments.empty else 0.0
    current = monthly.iloc[-1]
    previous = monthly.iloc[-2] if len(monthly) > 1 else current
    gap_ratio = (collections_gap / total_invoiced) if total_invoiced else 0.0

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Revenue Invoiced (€)", euro(total_invoiced), f"{current['invoiced'] - previous['invoiced']:,.0f}")
    col2.metric("Total Cash Collected (€)", euro(total_collected), f"{current['collected'] - previous['collected']:,.0f}")
    col3.metric("Collections Gap (€)", euro(collections_gap), f"{gap_ratio:.1%} gap", delta_color="inverse" if gap_ratio > 0.10 else "normal")
    col4.metric("Net Cash Flow (€)", euro(net_cash_flow), f"{current['net_cash_flow'] - previous['net_cash_flow']:,.0f}", delta_color="normal" if net_cash_flow >= 0 else "inverse")
    col5.metric("Number of Overdue Invoices", overdue_count, f"{overdue_count}", delta_color="inverse" if overdue_count > 0 else "normal")
    col6.metric("Average Payment Delay (days)", f"{avg_delay:.1f}", f"{avg_delay:.1f}")


def render_cash_flow_trends(monthly: pd.DataFrame) -> None:
    lowest_month = monthly.loc[monthly["net_cash_flow"].idxmin()]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=monthly["month"], y=monthly["collected"], name="Income", marker_color=ACCENT))
    fig.add_trace(go.Bar(x=monthly["month"], y=monthly["expenses"], name="Expenses", marker_color="#ff7f0e"))
    fig.add_trace(go.Scatter(x=monthly["month"], y=monthly["net_cash_flow"], mode="lines+markers", name="Net Cash Flow", line={"color": GREEN, "width": 3}, yaxis="y2"))
    fig.update_layout(
        barmode="group",
        yaxis2={"overlaying": "y", "side": "right", "title": "Net Cash Flow (€)"},
        annotations=[{"x": lowest_month["month"], "y": lowest_month["net_cash_flow"], "text": f"Lowest month: {lowest_month['month'].strftime('%b %Y')}", "showarrow": True, "arrowhead": 2, "font": {"color": TEXT_COLOR}}],
    )
    st.plotly_chart(apply_dark_layout(fig, "Monthly Income vs Expenses with Net Cash Flow", "Month", "Income / Expenses (€)"), use_container_width=True)

    forecast_df = forecast_cash_flow(monthly[["month", "net_cash_flow"]], months_ahead=3)
    forecast_fig = go.Figure()
    forecast_fig.add_trace(go.Scatter(x=monthly["month"], y=monthly["net_cash_flow"], mode="lines+markers", name="Historical Net Cash Flow", line={"color": ACCENT, "width": 3}))
    forecast_fig.add_trace(go.Scatter(x=forecast_df["month"], y=forecast_df["forecast_net_cash_flow"], mode="lines+markers", name="Forecast", line={"color": "#17becf", "width": 3, "dash": "dash"}))
    forecast_fig.add_trace(go.Scatter(x=pd.concat([forecast_df["month"], forecast_df["month"][::-1]]), y=pd.concat([forecast_df["upper_confidence"], forecast_df["lower_confidence"][::-1]]), fill="toself", fillcolor="rgba(31, 119, 180, 0.18)", line={"color": "rgba(255,255,255,0)"}, name="Confidence Band"))
    st.markdown("#### Forecast")
    st.plotly_chart(apply_dark_layout(forecast_fig, "3-Month Cash Flow Forecast", "Month", "Net Cash Flow (€)"), use_container_width=True)
    st.caption("Forecast is based on linear trend only and is for demonstration purposes")


def render_client_analysis(invoices: pd.DataFrame, payments: pd.DataFrame) -> None:
    client_summary = (
        invoices.groupby("client_name", as_index=False)
        .agg(total_invoiced=("invoice_amount", "sum"), invoice_count=("invoice_id", "count"))
        .merge(payments.groupby("client_name", as_index=False)["payment_amount"].sum().rename(columns={"payment_amount": "total_paid"}), on="client_name", how="left")
        .fillna({"total_paid": 0})
    )
    delay_frame = payments.assign(delay_days=(payments["payment_date"] - payments["due_date"]).dt.days).groupby("client_name", as_index=False)["delay_days"].mean().rename(columns={"delay_days": "avg_delay_days"})
    client_summary = client_summary.merge(delay_frame, on="client_name", how="left").fillna({"avg_delay_days": 0})
    client_summary["outstanding_balance"] = client_summary["total_invoiced"] - client_summary["total_paid"]
    client_summary["risk_level"] = np.select(
        [(client_summary["outstanding_balance"] > 15000) | (client_summary["avg_delay_days"] > 18), (client_summary["outstanding_balance"] > 5000) | (client_summary["avg_delay_days"] > 10)],
        ["High", "Medium"],
        default="Low",
    )

    bar_fig = px.bar(client_summary.sort_values("total_invoiced", ascending=True), x="total_invoiced", y="client_name", orientation="h", title="Top Clients by Total Revenue", labels={"total_invoiced": "Total Revenue (€)", "client_name": "Client"}, color="total_invoiced", color_continuous_scale="Blues")
    bar_fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(apply_dark_layout(bar_fig, "Top Clients by Total Revenue", "Revenue (€)", "Client"), use_container_width=True)

    scatter_fig = px.scatter(client_summary, x="total_invoiced", y="avg_delay_days", size="invoice_count", color="outstanding_balance", hover_name="client_name", title="Client Revenue vs Average Payment Delay", labels={"total_invoiced": "Total Revenue (€)", "avg_delay_days": "Average Payment Delay (days)", "invoice_count": "Invoices"}, color_continuous_scale="RdYlBu_r")
    st.plotly_chart(apply_dark_layout(scatter_fig, "Client Revenue vs Average Payment Delay", "Revenue (€)", "Average Delay (days)"), use_container_width=True)

    display = client_summary.sort_values("total_invoiced", ascending=False).rename(columns={"client_name": "Client name", "risk_level": "Risk Level"}).copy()
    display["Total Invoiced"] = display["total_invoiced"].map(euro)
    display["Total Paid"] = display["total_paid"].map(euro)
    display["Outstanding Balance"] = display["outstanding_balance"].map(euro)
    display["Avg Delay (days)"] = display["avg_delay_days"].round(1)
    st.dataframe(display[["Client name", "Total Invoiced", "Total Paid", "Outstanding Balance", "Avg Delay (days)", "Risk Level"]].style.map(lambda value: "background-color: #7f1d1d; color: white" if value == "High" else "background-color: #78350f; color: white" if value == "Medium" else "background-color: #14532d; color: white", subset=["Risk Level"]), use_container_width=True, hide_index=True)


def render_expense_analysis(expenses: pd.DataFrame) -> None:
    expense_breakdown = expenses.groupby("category", as_index=False)["amount"].sum()
    monthly_category = expenses.assign(month=expenses["expense_date"].dt.to_period("M").dt.to_timestamp()).groupby(["month", "category"], as_index=False)["amount"].sum()
    growth = monthly_category.sort_values("month").groupby("category").agg(first=("amount", "first"), last=("amount", "last")).assign(growth=lambda frame: frame["last"] - frame["first"]).reset_index().sort_values("growth", ascending=False)
    fastest = growth.iloc[0]

    donut_fig = px.pie(expense_breakdown, values="amount", names="category", hole=0.55, title="Expense Breakdown by Category", color_discrete_sequence=px.colors.sequential.Blues_r)
    st.plotly_chart(apply_dark_layout(donut_fig, "Expense Breakdown by Category", "", ""), use_container_width=True)
    line_fig = px.line(monthly_category, x="month", y="amount", color="category", markers=True, title="Monthly Expense Trend by Category", labels={"month": "Month", "amount": "Expense (€)", "category": "Category"})
    st.plotly_chart(apply_dark_layout(line_fig, "Monthly Expense Trend by Category", "Month", "Expense (€)"), use_container_width=True)
    st.info(f"Fastest-growing expense category: {fastest['category']} with a growth of {euro(float(fastest['growth']))} between the first and last visible month.")


def render_receivables_tracker(invoices: pd.DataFrame) -> None:
    tracker = invoices.copy()
    tracker["days_overdue"] = np.where(tracker["status"] == "overdue", (pd.Timestamp("2024-12-31") - tracker["due_date"]).dt.days, 0)
    overdue_total = float(tracker.loc[tracker["status"] == "overdue", "invoice_amount"].sum())
    overdue_count = int((tracker["status"] == "overdue").sum())
    st.markdown(f"There are **{overdue_count} overdue invoices** totalling **{euro(overdue_total)}**.")
    display = tracker.rename(columns={"client_name": "Client", "invoice_id": "Invoice #", "invoice_amount": "Amount", "due_date": "Due Date", "days_overdue": "Days Overdue", "status": "Status"})[["Client", "Invoice #", "Amount", "Due Date", "Days Overdue", "Status"]].copy()
    display["Due Date"] = display["Due Date"].dt.strftime("%Y-%m-%d")
    display["Amount"] = display["Amount"].map(euro)

    def style_rows(row: pd.Series) -> list[str]:
        status = row["Status"]
        if status == "overdue":
            color = "background-color: #7f1d1d; color: white"
        elif status == "pending":
            color = "background-color: #92400e; color: white"
        else:
            color = "background-color: #14532d; color: white"
        return [color] * len(row)

    st.dataframe(display.style.apply(style_rows, axis=1), use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="CashFlow Insight Dashboard", page_icon="💰", layout="wide")
    st.title("CashFlow Insight Dashboard")
    st.caption("Interactive finance analytics dashboard for receivables, expenses, and cash-flow storytelling.")
    frames = prepare_filtered_frames()
    invoices = frames["invoices"]
    payments = frames["payments"]
    expenses = frames["expenses"]
    monthly = build_monthly_summary(invoices, payments, expenses, frames["selected_periods"])

    executive_tab, cashflow_tab, client_tab, expense_tab, receivables_tab = st.tabs(["Executive Summary", "Cash Flow Trends", "Client Analysis", "Expense Analysis", "Invoice & Receivables Tracker"])
    with executive_tab:
        render_executive_summary(monthly, invoices, payments, expenses)
    with cashflow_tab:
        render_cash_flow_trends(monthly)
    with client_tab:
        render_client_analysis(invoices, payments)
    with expense_tab:
        render_expense_analysis(expenses)
    with receivables_tab:
        render_receivables_tracker(invoices)


if __name__ == "__main__":
    main()
