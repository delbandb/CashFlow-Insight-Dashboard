DROP TABLE IF EXISTS clients;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS expenses;

CREATE TABLE clients (
    client_id TEXT PRIMARY KEY,
    client_name TEXT NOT NULL,
    industry TEXT NOT NULL,
    country TEXT NOT NULL,
    contract_type TEXT NOT NULL,
    start_date TEXT NOT NULL
);

CREATE TABLE invoices (
    invoice_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    issue_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    invoice_amount REAL NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients (client_id)
);

CREATE TABLE payments (
    payment_id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    payment_date TEXT NOT NULL,
    payment_amount REAL NOT NULL,
    payment_status TEXT NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices (invoice_id)
);

CREATE TABLE expenses (
    expense_id TEXT PRIMARY KEY,
    expense_date TEXT NOT NULL,
    department TEXT NOT NULL,
    category TEXT NOT NULL,
    vendor TEXT NOT NULL,
    amount REAL NOT NULL
);
