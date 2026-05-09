from __future__ import annotations

import pandas as pd

from app.db import read_sql_frame


MONTHLY_CASHFLOW_SQL = """
WITH monthly_income AS (
    SELECT
        strftime('%Y-%m-01', payment_date) AS month,
        SUM(payment_amount) AS income
    FROM payments
    GROUP BY strftime('%Y-%m-01', payment_date)
),
monthly_expenses AS (
    SELECT
        strftime('%Y-%m-01', expense_date) AS month,
        SUM(amount) AS expenses
    FROM expenses
    GROUP BY strftime('%Y-%m-01', expense_date)
),
all_months AS (
    SELECT month FROM monthly_income
    UNION
    SELECT month FROM monthly_expenses
)
SELECT
    all_months.month,
    ROUND(COALESCE(monthly_income.income, 0), 2) AS income,
    ROUND(COALESCE(monthly_expenses.expenses, 0), 2) AS expenses,
    ROUND(COALESCE(monthly_income.income, 0) - COALESCE(monthly_expenses.expenses, 0), 2) AS net_cash_flow
FROM all_months
LEFT JOIN monthly_income ON monthly_income.month = all_months.month
LEFT JOIN monthly_expenses ON monthly_expenses.month = all_months.month
ORDER BY all_months.month;
"""


TOP_CLIENTS_BY_REVENUE_SQL = """
SELECT
    c.client_name,
    ROUND(SUM(i.invoice_amount), 2) AS total_invoiced,
    COUNT(*) AS invoice_count
FROM invoices AS i
JOIN clients AS c ON c.client_id = i.client_id
GROUP BY c.client_id, c.client_name
ORDER BY total_invoiced DESC, c.client_name ASC
LIMIT ?;
"""


OVERDUE_INVOICES_SQL = """
SELECT
    c.client_name,
    i.invoice_id,
    ROUND(i.invoice_amount, 2) AS amount,
    i.issue_date,
    i.due_date,
    CAST(julianday('2024-12-31') - julianday(i.due_date) AS INTEGER) AS days_overdue,
    i.status
FROM invoices AS i
JOIN clients AS c ON c.client_id = i.client_id
WHERE i.status = 'overdue'
ORDER BY i.due_date ASC, c.client_name ASC;
"""


EXPENSE_BY_CATEGORY_SQL = """
SELECT
    category,
    ROUND(SUM(amount), 2) AS total_amount
FROM expenses
GROUP BY category
ORDER BY total_amount DESC, category ASC;
"""


AVG_PAYMENT_DELAY_BY_CLIENT_SQL = """
SELECT
    c.client_name,
    ROUND(AVG(julianday(p.payment_date) - julianday(i.due_date)), 2) AS avg_payment_delay_days,
    COUNT(i.invoice_id) AS invoice_count,
    ROUND(SUM(i.invoice_amount), 2) AS total_invoiced,
    ROUND(COALESCE(SUM(p.payment_amount), 0), 2) AS total_paid
FROM invoices AS i
JOIN clients AS c ON c.client_id = i.client_id
LEFT JOIN payments AS p ON p.invoice_id = i.invoice_id
WHERE p.payment_date IS NOT NULL
GROUP BY c.client_id, c.client_name
ORDER BY total_invoiced DESC, avg_payment_delay_days DESC;
"""


COLLECTIONS_GAP_SQL = """
WITH invoiced AS (
    SELECT ROUND(COALESCE(SUM(invoice_amount), 0), 2) AS total_invoiced
    FROM invoices
),
collected AS (
    SELECT ROUND(COALESCE(SUM(payment_amount), 0), 2) AS total_collected
    FROM payments
)
SELECT
    invoiced.total_invoiced,
    collected.total_collected,
    ROUND(invoiced.total_invoiced - collected.total_collected, 2) AS collections_gap
FROM invoiced
CROSS JOIN collected;
"""


def get_monthly_cashflow() -> pd.DataFrame:
    return read_sql_frame(MONTHLY_CASHFLOW_SQL)


def get_top_clients_by_revenue(n: int = 10) -> pd.DataFrame:
    return read_sql_frame(TOP_CLIENTS_BY_REVENUE_SQL, params=(n,))


def get_overdue_invoices() -> pd.DataFrame:
    return read_sql_frame(OVERDUE_INVOICES_SQL)


def get_expense_by_category() -> pd.DataFrame:
    return read_sql_frame(EXPENSE_BY_CATEGORY_SQL)


def get_avg_payment_delay_by_client() -> pd.DataFrame:
    return read_sql_frame(AVG_PAYMENT_DELAY_BY_CLIENT_SQL)


def get_collections_gap() -> pd.DataFrame:
    return read_sql_frame(COLLECTIONS_GAP_SQL)
