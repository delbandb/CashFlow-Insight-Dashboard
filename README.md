# CashFlow Insight Dashboard

A finance analytics dashboard that turns synthetic invoice, payment, client, and expense data into a clear cash-flow story. The project is built to look like a small business intelligence workflow: generate demo finance data, load it into SQLite, analyze it with pandas and SQL, and present the results in Streamlit with Plotly charts.

## Why I Built It

I wanted a project that connects Python analysis with a real business problem: invoices are not the same as collected cash. This dashboard focuses on the questions a finance or operations team would ask first: how much has been invoiced, how much has actually been collected, which clients create risk, where expenses are growing, and which invoices need attention.

## Main Features

- Executive KPI view for invoiced revenue, collected cash, collections gap, net cash flow, overdue invoices, and average payment delay.
- Monthly cash-flow trend comparing collected income, expenses, and net cash flow.
- Simple three-month cash-flow forecast using a linear trend over historical monthly net cash flow.
- Client analysis showing revenue concentration, outstanding balance, average delay, and risk level.
- Expense analysis by category with monthly trends and fastest-growing cost category.
- Receivables tracker with overdue invoice status and days overdue.
- SQLite reporting layer with schema and reusable SQL queries.
- Automated tests for KPI calculations, overdue logic, forecasting, and expense aggregation.

## Tech Stack

| Area | Tools |
| --- | --- |
| Language | Python |
| Data analysis | pandas, numpy |
| Dashboard | Streamlit |
| Visualization | Plotly |
| Database | SQLite |
| Testing | pytest |

## Project Structure

```text
cashflow-insight-dashboard/
|-- app/
|   |-- analysis.py          # KPI logic, overdue detection, forecasting
|   |-- build_database.py    # Demo data and database builder
|   |-- dashboard.py         # Streamlit dashboard UI
|   |-- data_loader.py       # CSV loading helpers
|   |-- db.py                # SQLite setup and seeding
|   `-- sql_queries.py       # Reporting queries used by the app
|-- data/                    # Synthetic CSV data
|-- docs/                    # SQL examples and visual notes
|-- sql/schema.sql           # SQLite schema
|-- tests/test_analysis.py   # Analysis tests
|-- requirements.txt
`-- streamlit_app.py         # Streamlit Cloud entry point
```

## Run Locally

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m app.build_database
.venv/Scripts/streamlit run streamlit_app.py
```

On macOS or Linux, replace `.venv/Scripts/python` with `.venv/bin/python` and `.venv/Scripts/streamlit` with `.venv/bin/streamlit`.

## Run Tests

```bash
pytest
```

The tests cover the parts of the project that matter most for confidence: KPI math, overdue invoice detection, forecast output shape, expense totals, and payment sanity checks.

## Example Business Questions

- What is the difference between invoiced revenue and collected cash?
- Which clients generate the most revenue but also create collection risk?
- Which months put pressure on net cash flow?
- Which expense categories are growing fastest?
- Which invoices are overdue and need follow-up?

## Design Decisions

- I used synthetic data so the project is safe to share publicly while still telling a realistic finance story.
- I kept the forecasting model intentionally simple because it should be easy to explain in an interview.
- I separated data loading, analysis, SQL queries, and UI code so the project does not become one long notebook.
- I included both pandas and SQL paths because finance reporting often lives between spreadsheets, databases, and dashboards.

## Roadmap

- Add CSV upload so users can test their own finance data.
- Add PostgreSQL support alongside SQLite.
- Add downloadable monthly finance reports.
- Improve forecasting with seasonality-aware methods.
- Add more tests around SQL query outputs and dashboard data preparation.

## Data Disclaimer

All data is synthetically generated for demonstration purposes. It does not represent any real company, client, invoice, payment, or expense.
