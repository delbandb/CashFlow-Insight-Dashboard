from __future__ import annotations


SUMMARY_QUERY = """
WITH invoice_totals AS (
    SELECT COALESCE(SUM(invoice_amount), 0) AS invoiced_income
    FROM invoices
),
payment_totals AS (
    SELECT COALESCE(SUM(payment_amount), 0) AS paid_income
    FROM payments
),
expense_totals AS (
    SELECT COALESCE(SUM(amount), 0) AS total_expenses
    FROM expenses
),
client_totals AS (
    SELECT COUNT(DISTINCT client_id) AS active_clients
    FROM clients
),
overdue_totals AS (
    SELECT COUNT(*) AS overdue_invoice_count
    FROM invoices
    WHERE status IN ('late', 'overdue')
)
SELECT
    payment_totals.paid_income,
    invoice_totals.invoiced_income,
    expense_totals.total_expenses,
    payment_totals.paid_income - expense_totals.total_expenses AS net_cash_flow,
    client_totals.active_clients,
    overdue_totals.overdue_invoice_count
FROM invoice_totals
CROSS JOIN payment_totals
CROSS JOIN expense_totals
CROSS JOIN client_totals
CROSS JOIN overdue_totals;
"""


MONTHLY_CASH_FLOW_QUERY = """
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
    COALESCE(monthly_income.income, 0) AS income,
    COALESCE(monthly_expenses.expenses, 0) AS expenses,
    COALESCE(monthly_income.income, 0) - COALESCE(monthly_expenses.expenses, 0) AS net_cash_flow
FROM all_months
LEFT JOIN monthly_income ON monthly_income.month = all_months.month
LEFT JOIN monthly_expenses ON monthly_expenses.month = all_months.month
ORDER BY all_months.month;
"""


TOP_CLIENTS_QUERY = """
SELECT
    clients.client_name,
    clients.industry,
    SUM(invoices.invoice_amount) AS invoice_amount
FROM invoices
JOIN clients ON clients.client_id = invoices.client_id
GROUP BY clients.client_name, clients.industry
ORDER BY invoice_amount DESC, clients.client_name ASC;
"""


LATE_PAYMENT_QUERY = """
SELECT
    clients.client_name,
    ROUND(AVG(julianday(payments.payment_date) - julianday(invoices.due_date)), 2) AS average_delay_days,
    SUM(
        CASE
            WHEN julianday(payments.payment_date) - julianday(invoices.due_date) > 0 THEN 1
            ELSE 0
        END
    ) AS late_payment_count
FROM invoices
JOIN clients ON clients.client_id = invoices.client_id
LEFT JOIN payments ON payments.invoice_id = invoices.invoice_id
WHERE payments.payment_date IS NOT NULL
GROUP BY clients.client_name
ORDER BY late_payment_count DESC, average_delay_days DESC;
"""


EXPENSE_CATEGORY_QUERY = """
SELECT
    category,
    SUM(amount) AS amount
FROM expenses
GROUP BY category
ORDER BY amount DESC, category ASC;
"""


OVERDUE_INVOICES_QUERY = """
SELECT
    invoices.invoice_id,
    clients.client_name,
    invoices.issue_date,
    invoices.due_date,
    invoices.invoice_amount,
    invoices.status
FROM invoices
JOIN clients ON clients.client_id = invoices.client_id
WHERE invoices.status IN ('late', 'overdue')
ORDER BY invoices.due_date ASC;
"""
