/*
CashFlow Insight Dashboard - sample recruiter-friendly SQL

This file contains six reporting queries that mirror the dashboard's business logic.
Each query focuses on a finance question that matters in real operations:
1. How cash collection compares with spending over time.
2. Which clients drive the most billed revenue.
3. Which invoices are overdue and how long they have been outstanding.
4. Which expense categories consume the most budget.
5. Which clients tend to pay late.
6. Whether billed revenue is converting into collected cash.
*/

-- 1. Monthly cash flow:
-- Combines collected income and operating expenses by month to show net cash flow.
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
    all_months.month,
    ROUND(COALESCE(monthly_income.income, 0), 2) AS income,
    ROUND(COALESCE(monthly_expenses.expenses, 0), 2) AS expenses,
    ROUND(COALESCE(monthly_income.income, 0) - COALESCE(monthly_expenses.expenses, 0), 2) AS net_cash_flow
FROM all_months
LEFT JOIN monthly_income ON monthly_income.month = all_months.month
LEFT JOIN monthly_expenses ON monthly_expenses.month = all_months.month
ORDER BY all_months.month;

-- 2. Top clients by revenue:
-- Ranks clients by total invoiced value to show concentration risk and account importance.
SELECT
    c.client_name,
    ROUND(SUM(i.invoice_amount), 2) AS total_invoiced,
    COUNT(*) AS invoice_count
FROM invoices AS i
JOIN clients AS c ON c.client_id = i.client_id
GROUP BY c.client_id, c.client_name
ORDER BY total_invoiced DESC, c.client_name ASC
LIMIT 10;

-- 3. Overdue invoices:
-- Lists unpaid invoices that are already past due and calculates how many days overdue they are.
SELECT
    c.client_name,
    i.invoice_id,
    ROUND(i.invoice_amount, 2) AS amount,
    i.due_date,
    CAST(julianday('2024-12-31') - julianday(i.due_date) AS INTEGER) AS days_overdue,
    i.status
FROM invoices AS i
JOIN clients AS c ON c.client_id = i.client_id
WHERE i.status = 'overdue'
ORDER BY i.due_date ASC, c.client_name ASC;

-- 4. Expense totals by category:
-- Aggregates operating spend into business categories to surface the main cost drivers.
SELECT
    category,
    ROUND(SUM(amount), 2) AS total_amount
FROM expenses
GROUP BY category
ORDER BY total_amount DESC, category ASC;

-- 5. Average payment delay by client:
-- Measures how long each client takes to pay relative to invoice due dates.
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

-- 6. Collections gap:
-- Compares total billed revenue with collected cash to highlight working-capital pressure.
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
