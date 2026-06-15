"""Drop SQLAlchemy-only tables from ca_lab.db after web_ui removal."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "ca_lab.db"


def main() -> None:
    if not DB_PATH.exists():
        print("No database file found; nothing to clean.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]
    print("Tables before:", tables)

    cur.execute("PRAGMA foreign_keys=OFF")
    for table in tables:
        if table != "sqlite_sequence":
            cur.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"Dropped {table}")

    conn.commit()
    conn.close()
    print("Database cleanup complete. Run init_db + seed to recreate.")


if __name__ == "__main__":
    main()
