PRAGMA foreign_keys = OFF;

-- Reset tables so the synthetic dataset can be regenerated cleanly.
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS expenses;
DROP TABLE IF EXISTS clients;

PRAGMA foreign_keys = ON;

-- Master list of clients used for billing and receivables analysis.
CREATE TABLE clients (
    client_id TEXT PRIMARY KEY,
    client_name TEXT NOT NULL,
    industry TEXT NOT NULL,
    country TEXT NOT NULL,
    contract_type TEXT NOT NULL,
    start_date TEXT NOT NULL
);

-- Invoices represent billed revenue and the receivable position.
CREATE TABLE invoices (
    invoice_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    issue_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    invoice_amount REAL NOT NULL CHECK (invoice_amount >= 0),
    status TEXT NOT NULL CHECK (status IN ('paid', 'pending', 'overdue')),
    FOREIGN KEY (client_id) REFERENCES clients (client_id)
);

-- Payments capture collected cash against invoices.
CREATE TABLE payments (
    payment_id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    payment_date TEXT NOT NULL,
    payment_amount REAL NOT NULL CHECK (payment_amount >= 0),
    payment_status TEXT NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices (invoice_id)
);

-- Expenses hold operating cost transactions by category.
CREATE TABLE expenses (
    expense_id TEXT PRIMARY KEY,
    expense_date TEXT NOT NULL,
    department TEXT NOT NULL,
    category TEXT NOT NULL,
    vendor TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount >= 0)
);

-- Indexes for common dashboard and reporting filters.
CREATE INDEX idx_invoices_client_id ON invoices (client_id);
CREATE INDEX idx_invoices_due_date ON invoices (due_date);
CREATE INDEX idx_invoices_status ON invoices (status);
CREATE INDEX idx_payments_invoice_id ON payments (invoice_id);
CREATE INDEX idx_payments_payment_date ON payments (payment_date);
CREATE INDEX idx_expenses_expense_date ON expenses (expense_date);
CREATE INDEX idx_expenses_category ON expenses (category);
