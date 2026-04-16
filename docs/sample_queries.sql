-- Monthly cash flow trend
WITH monthly_income AS (
    SELECT strftime('%Y-%m-01', payment_date) AS month, SUM(payment_amount) AS income
    FROM payments
    GROUP BY strftime('%Y-%m-01', payment_date)
),
monthly_expenses AS (
    SELECT strftime('%Y-%m-01', expense_date) AS month, SUM(amount) AS expenses
    FROM expenses
    GROUP BY strftime('%Y-%m-01', expense_date)
),
all_months AS (
    SELECT month FROM monthly_income
    UNION
    SELECT month FROM monthly_expenses
)
SELECT
    all_months.month AS month,
    COALESCE(monthly_income.income, 0) AS income,
    COALESCE(monthly_expenses.expenses, 0) AS expenses,
    COALESCE(monthly_income.income, 0) - COALESCE(monthly_expenses.expenses, 0) AS net_cash_flow
FROM all_months
LEFT JOIN monthly_income ON monthly_income.month = all_months.month
LEFT JOIN monthly_expenses ON monthly_expenses.month = all_months.month
ORDER BY all_months.month;

-- Top clients by revenue
SELECT
    clients.client_name,
    SUM(invoices.invoice_amount) AS total_revenue
FROM invoices
JOIN clients ON clients.client_id = invoices.client_id
GROUP BY clients.client_name
ORDER BY total_revenue DESC;

-- Late payment frequency
SELECT
    clients.client_name,
    SUM(CASE WHEN julianday(payments.payment_date) - julianday(invoices.due_date) > 0 THEN 1 ELSE 0 END) AS late_payments
FROM invoices
JOIN clients ON clients.client_id = invoices.client_id
LEFT JOIN payments ON payments.invoice_id = invoices.invoice_id
GROUP BY clients.client_name
ORDER BY late_payments DESC;
