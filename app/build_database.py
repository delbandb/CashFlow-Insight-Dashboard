# All data is synthetically generated for demonstration purposes
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random

import pandas as pd

from app.db import seed_database

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
REFERENCE_DATE = pd.Timestamp("2024-12-31")


@dataclass(frozen=True)
class ClientProfile:
    client_id: str
    client_name: str
    industry: str
    country: str
    contract_type: str
    start_date: str
    base_amount: int
    payment_delay: int
    amount_multiplier: float


CLIENTS: list[ClientProfile] = [
    ClientProfile("C001", "Nexum Group", "Enterprise Technology", "Germany", "Retainer", "2023-04-15", 18000, 4, 1.65),
    ClientProfile("C002", "Solara Retail", "Retail", "Spain", "Project", "2023-09-01", 7200, 6, 1.15),
    ClientProfile("C003", "Brindlewick & Co", "Professional Services", "United Kingdom", "Project", "2024-01-10", 5400, 28, 0.95),
    ClientProfile("C004", "Oakridge Health", "Healthcare", "Netherlands", "Retainer", "2023-12-20", 6800, 24, 1.0),
    ClientProfile("C005", "Northstar Logistics", "Logistics", "Germany", "Retainer", "2022-11-03", 8500, 8, 1.05),
    ClientProfile("C006", "Asteron Media", "Marketing", "France", "Project", "2024-02-05", 4300, 12, 0.9),
    ClientProfile("C007", "Cobalt Manufacturing", "Manufacturing", "Italy", "Retainer", "2023-06-18", 9100, 7, 1.08),
    ClientProfile("C008", "Harbor & Finch", "Hospitality", "Portugal", "Project", "2024-03-12", 3600, 10, 0.85),
    ClientProfile("C009", "Velora Foods", "Consumer Goods", "Belgium", "Retainer", "2023-08-08", 7600, 5, 1.02),
    ClientProfile("C010", "Helix Advisory", "Consulting", "Ireland", "Project", "2024-04-22", 5200, 14, 0.92),
]


MONTHLY_CLIENT_PLAN: dict[str, list[str]] = {
    "2024-01": ["C001", "C002", "C003", "C004", "C005", "C007", "C009"],
    "2024-02": ["C001", "C002", "C004", "C005", "C006", "C007", "C010"],
    "2024-03": ["C001", "C002", "C003", "C005", "C006", "C008", "C009"],
    "2024-04": ["C001", "C002", "C004", "C005", "C007", "C009", "C010"],
    "2024-05": ["C001", "C002", "C003", "C004", "C006", "C007", "C009"],
    "2024-06": ["C001", "C002", "C004", "C005", "C007", "C008", "C010"],
    "2024-07": ["C001", "C002", "C003", "C004", "C006", "C008", "C009"],
    "2024-08": ["C001", "C002", "C003", "C004", "C005", "C007", "C010"],
    "2024-09": ["C001", "C003", "C004", "C005", "C006", "C008", "C009"],
    "2024-10": ["C001", "C002", "C004", "C005", "C007", "C009", "C010"],
    "2024-11": ["C001", "C002", "C003", "C005", "C006", "C007", "C009"],
    "2024-12": ["C001", "C002", "C004", "C005", "C007", "C008", "C010"],
}


EXPENSE_PLAN: dict[str, tuple[str, str, int]] = {
    "Salaries": ("People Ops", "Payroll Partners", 18500),
    "Software": ("Technology", "CloudDock", 2800),
    "Marketing": ("Growth", "SignalForge", 2200),
    "Rent": ("Operations", "Riverside Offices", 5200),
    "Travel": ("Operations", "SkyBridge Travel", 1100),
    "Utilities": ("Operations", "City Utilities", 950),
    "Legal": ("Finance", "Lumen Legal", 1400),
}


def _quarter_adjustment(month: int) -> float:
    if month in (7, 8, 9):
        return 0.78
    if month in (10, 11, 12):
        return 1.08
    return 1.0


def build_clients() -> pd.DataFrame:
    return pd.DataFrame([client.__dict__ for client in CLIENTS]).drop(
        columns=["base_amount", "payment_delay", "amount_multiplier"]
    )


def build_invoices() -> pd.DataFrame:
    rng = random.Random(42)
    records: list[dict[str, object]] = []
    invoice_counter = 1
    overdue_slots = {
        "2024-08": {"C003"},
        "2024-09": {"C004"},
        "2024-10": {"C003", "C004"},
        "2024-11": {"C003"},
    }
    pending_slots = {"2024-12": {"C008", "C010"}}

    for month_key, client_ids in MONTHLY_CLIENT_PLAN.items():
        month_start = pd.Timestamp(f"{month_key}-01")
        month_factor = _quarter_adjustment(month_start.month)
        for client_id in client_ids:
            profile = next(client for client in CLIENTS if client.client_id == client_id)
            issue_day = min(25, 2 + (invoice_counter * 3) % 24)
            issue_date = month_start + pd.Timedelta(days=issue_day - 1)
            payment_terms = rng.choice([14, 21, 30, 45])
            due_date = issue_date + pd.Timedelta(days=payment_terms)
            variability = rng.uniform(0.82, 1.24)
            amount = profile.base_amount * profile.amount_multiplier * month_factor * variability
            amount = max(500, min(25000, round(amount / 50) * 50))
            status = "paid"
            if client_id in overdue_slots.get(month_key, set()):
                status = "overdue"
            elif client_id in pending_slots.get(month_key, set()) or due_date > REFERENCE_DATE:
                status = "pending"

            records.append(
                {
                    "invoice_id": f"INV-{invoice_counter:04d}",
                    "client_id": client_id,
                    "issue_date": issue_date.date().isoformat(),
                    "due_date": due_date.date().isoformat(),
                    "invoice_amount": float(amount),
                    "status": status,
                }
            )
            invoice_counter += 1

    return pd.DataFrame(records)


def build_payments(invoices: pd.DataFrame) -> pd.DataFrame:
    rng = random.Random(84)
    client_lookup = {client.client_id: client for client in CLIENTS}
    records: list[dict[str, object]] = []

    for payment_counter, invoice in enumerate(invoices.itertuples(index=False), start=1):
        if invoice.status != "paid":
            continue
        profile = client_lookup[invoice.client_id]
        due_date = pd.Timestamp(invoice.due_date)
        payment_date = due_date + pd.Timedelta(days=profile.payment_delay + rng.randint(-3, 4))
        payment_date = max(payment_date, pd.Timestamp(invoice.issue_date) + pd.Timedelta(days=5))
        records.append(
            {
                "payment_id": f"PAY-{payment_counter:04d}",
                "invoice_id": invoice.invoice_id,
                "payment_date": payment_date.date().isoformat(),
                "payment_amount": float(invoice.invoice_amount),
                "payment_status": "settled",
            }
        )

    return pd.DataFrame(records)


def build_expenses() -> pd.DataFrame:
    rng = random.Random(126)
    records: list[dict[str, object]] = []
    expense_counter = 1
    growth_weights = {category: 1.0 for category in EXPENSE_PLAN}
    growth_weights["Marketing"] = 1.35
    growth_weights["Travel"] = 1.25
    growth_weights["Software"] = 1.15

    for month in pd.date_range("2024-01-01", "2024-12-01", freq="MS"):
        q3_multiplier = 1.18 if month.month in (7, 8, 9) else 1.0
        year_end_multiplier = 1.08 if month.month in (11, 12) else 1.0
        for category, (department, vendor, base_amount) in EXPENSE_PLAN.items():
            growth_factor = 1 + ((month.month - 1) * 0.018 * growth_weights[category])
            noise = rng.uniform(0.94, 1.08)
            amount = base_amount * growth_factor * noise * q3_multiplier * year_end_multiplier
            if category == "Marketing" and month.month in (7, 8, 9):
                amount *= 1.35
            if category == "Travel" and month.month in (7, 8, 9):
                amount *= 1.28
            expense_date = month + pd.Timedelta(days=min(25, 3 + expense_counter % 24))
            records.append(
                {
                    "expense_id": f"EXP-{expense_counter:04d}",
                    "expense_date": expense_date.date().isoformat(),
                    "department": department,
                    "category": category,
                    "vendor": vendor,
                    "amount": float(round(amount, 2)),
                }
            )
            expense_counter += 1

    return pd.DataFrame(records)


def generate_demo_data() -> dict[str, pd.DataFrame]:
    clients = build_clients()
    invoices = build_invoices()
    payments = build_payments(invoices)
    expenses = build_expenses()
    return {
        "clients": clients,
        "invoices": invoices,
        "payments": payments,
        "expenses": expenses,
    }


def write_demo_csvs() -> dict[str, pd.DataFrame]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = generate_demo_data()
    for name, frame in data.items():
        frame.to_csv(DATA_DIR / f"{name}.csv", index=False)
    return data


def main() -> None:
    write_demo_csvs()
    db_path = seed_database()
    print(f"SQLite database created at: {db_path}")


if __name__ == "__main__":
    main()
