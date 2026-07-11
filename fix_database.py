"""Fix CA Lab database schema by adding missing columns."""

import sqlite3
from pathlib import Path

DB_PATH = Path("ca_lab.db")


def fix_database():
    """Add missing columns to existing database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check and add missing columns to rules table
    cursor.execute("PRAGMA table_info(rules)")
    columns = {row[1] for row in cursor.fetchall()}

    if "is_builtin" not in columns:
        print("Adding is_builtin column to rules table...")
        cursor.execute("ALTER TABLE rules ADD COLUMN is_builtin BOOLEAN DEFAULT 0")
        print("[OK] Added is_builtin column")

    if "is_editable" not in columns:
        print("Adding is_editable column to rules table...")
        cursor.execute("ALTER TABLE rules ADD COLUMN is_editable BOOLEAN DEFAULT 1")
        print("[OK] Added is_editable column")

    if "description" not in columns:
        print("Adding description column to rules table...")
        cursor.execute("ALTER TABLE rules ADD COLUMN description TEXT")
        print("[OK] Added description column")

    if "category" not in columns:
        print("Adding category column to rules table...")
        cursor.execute("ALTER TABLE rules ADD COLUMN category TEXT DEFAULT 'experimental'")
        print("[OK] Added category column")

    if "updated_at" not in columns:
        print("Adding updated_at column to rules table...")
        cursor.execute("ALTER TABLE rules ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        print("[OK] Added updated_at column")

    # Check and add missing columns to custom_metrics table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='custom_metrics'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(custom_metrics)")
        metric_columns = {row[1] for row in cursor.fetchall()}

        if "is_builtin" not in metric_columns:
            print("Adding is_builtin column to custom_metrics table...")
            cursor.execute("ALTER TABLE custom_metrics ADD COLUMN is_builtin BOOLEAN DEFAULT 0")
            print("[OK] Added is_builtin column to custom_metrics")

        if "metric_type" not in metric_columns:
            print("Adding metric_type column to custom_metrics table...")
            cursor.execute(
                "ALTER TABLE custom_metrics ADD COLUMN metric_type TEXT NOT NULL DEFAULT 'formula'"
            )
            print("[OK] Added metric_type column")

        if "config_json" not in metric_columns:
            print("Adding config_json column to custom_metrics table...")
            cursor.execute("ALTER TABLE custom_metrics ADD COLUMN config_json TEXT DEFAULT '{}'")
            print("[OK] Added config_json column")

        if "is_editable" not in metric_columns:
            print("Adding is_editable column to custom_metrics table...")
            cursor.execute("ALTER TABLE custom_metrics ADD COLUMN is_editable BOOLEAN DEFAULT 1")
            print("[OK] Added is_editable column")

        if "updated_at" not in metric_columns:
            print("Adding updated_at column to custom_metrics table...")
            cursor.execute("ALTER TABLE custom_metrics ADD COLUMN updated_at TIMESTAMP")
            print("[OK] Added updated_at column")

    conn.commit()
    conn.close()
    print("\n[SUCCESS] Database schema fixed successfully!")


if __name__ == "__main__":
    if not DB_PATH.exists():
        print(f"❌ Database file not found: {DB_PATH}")
        print("The database will be created automatically when you start the server.")
    else:
        print(f"Fixing database schema: {DB_PATH}")
        fix_database()
