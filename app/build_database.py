from __future__ import annotations

from app.db import seed_database


if __name__ == "__main__":
    db_path = seed_database()
    print(f"SQLite database created at: {db_path}")
