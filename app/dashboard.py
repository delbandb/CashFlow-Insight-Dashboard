from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.analysis import build_metrics


st.set_page_config(
    page_title="CashFlow Insight Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
)


def euro(value: float) -> str:
    return f"EUR {value:,.0f}"


metrics = build_metrics()
summary = metrics["summary"]
monthly_cash_flow = metrics["monthly_cash_flow"]
revenue_by_client = metrics["revenue_by_client"]
late_payment_summary = metrics["late_payment_summary"]
expense_by_category = metrics["expense_by_category"]
dashboard_table = metrics["dashboard_table"]
overdue_invoices = metrics["overdue_invoices"]

st.title("CashFlow Insight Dashboard")
st.caption(
    "Interactive finance analytics project focused on client revenue, payments, expenses, and monthly cash flow."
)

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Paid Income", euro(summary["paid_income"]))
col2.metric("Invoiced Income", euro(summary["invoiced_income"]))
col3.metric("Total Expenses", euro(summary["total_expenses"]))
col4.metric("Net Cash Flow", euro(summary["net_cash_flow"]))
col5.metric("Active Clients", summary["active_clients"])
col6.metric("Overdue Invoices", summary["overdue_invoice_count"])

trend_fig = go.Figure()
trend_fig.add_trace(
    go.Scatter(
        x=monthly_cash_flow["month"],
        y=monthly_cash_flow["income"],
        mode="lines+markers",
        name="Income",
        line={"color": "#1f8a70", "width": 3},
    )
)
trend_fig.add_trace(
    go.Scatter(
        x=monthly_cash_flow["month"],
        y=monthly_cash_flow["expenses"],
        mode="lines+markers",
        name="Expenses",
        line={"color": "#c44536", "width": 3},
    )
)
trend_fig.add_trace(
    go.Bar(
        x=monthly_cash_flow["month"],
        y=monthly_cash_flow["net_cash_flow"],
        name="Net Cash Flow",
        marker_color="#1b4965",
        opacity=0.6,
    )
)
trend_fig.update_layout(
    title="Monthly Income, Expenses, and Net Cash Flow",
    xaxis_title="Month",
    yaxis_title="EUR",
    legend_title="Metric",
)

client_fig = px.bar(
    revenue_by_client,
    x="invoice_amount",
    y="client_name",
    orientation="h",
    title="Top Clients by Total Invoiced Revenue",
    labels={"invoice_amount": "Revenue (EUR)", "client_name": "Client"},
    color="invoice_amount",
    color_continuous_scale="Tealgrn",
)
client_fig.update_layout(coloraxis_showscale=False, yaxis={"categoryorder": "total ascending"})

expense_fig = px.pie(
    expense_by_category,
    values="amount",
    names="category",
    title="Expense Distribution by Category",
    hole=0.45,
)

late_fig = px.bar(
    late_payment_summary,
    x="client_name",
    y="late_payment_count",
    color="average_delay_days",
    title="Late Payment Frequency by Client",
    labels={"client_name": "Client", "late_payment_count": "Late Payments"},
    color_continuous_scale="OrRd",
)

top_row_left, top_row_right = st.columns((1.4, 1))
with top_row_left:
    st.plotly_chart(trend_fig, use_container_width=True)
with top_row_right:
    st.plotly_chart(expense_fig, use_container_width=True)

bottom_row_left, bottom_row_right = st.columns(2)
with bottom_row_left:
    st.plotly_chart(client_fig, use_container_width=True)
with bottom_row_right:
    st.plotly_chart(late_fig, use_container_width=True)

st.subheader("Monthly Finance Table")
st.dataframe(dashboard_table, use_container_width=True, hide_index=True)

st.subheader("Overdue or Late Invoices")
if overdue_invoices.empty:
    st.success("There are no late or overdue invoices in the current dataset.")
else:
    overdue_display = overdue_invoices[
        ["invoice_id", "client_name", "issue_date", "due_date", "invoice_amount", "status"]
    ].copy()
    overdue_display["issue_date"] = pd.to_datetime(overdue_display["issue_date"]).dt.strftime("%Y-%m-%d")
    overdue_display["due_date"] = pd.to_datetime(overdue_display["due_date"]).dt.strftime("%Y-%m-%d")
    st.dataframe(overdue_display, use_container_width=True, hide_index=True)

st.subheader("Key Insights")
st.markdown(
    """
- The company generated more invoiced revenue than collected cash, which highlights collection timing risk.
- Revenue is concentrated among a small number of clients, especially recurring accounts.
- Salaries remain the largest expense block, while advertising and IT purchases create secondary spikes.
- Late or overdue invoices provide a realistic example of why cash flow analysis matters beyond simple revenue totals.
"""
)
