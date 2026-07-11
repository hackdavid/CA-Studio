"""SQLite database for CA Lab web UI.

Async SQLite using aiosqlite for FastAPI compatibility.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import aiosqlite

DB_PATH = Path("ca_lab.db")


async def init_db() -> None:
    """Initialize database schema."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Rules table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                yaml_content TEXT NOT NULL,
                is_builtin BOOLEAN DEFAULT 0,
                is_editable BOOLEAN DEFAULT 1,
                description TEXT,
                category TEXT DEFAULT 'experimental',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sessions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rule_id INTEGER NOT NULL,
                board_width INTEGER DEFAULT 64,
                board_height INTEGER DEFAULT 64,
                neighbourhood TEXT DEFAULT 'moore8',
                num_states INTEGER DEFAULT 2,
                seed_config TEXT DEFAULT '{}',
                current_grid BLOB,
                current_step INTEGER DEFAULT 0,
                status TEXT DEFAULT 'paused',
                metrics_enabled TEXT DEFAULT '["density", "entropy"]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rule_id) REFERENCES rules(id)
            )
        """)

        # Session snapshots table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS session_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                grid_state BLOB,
                metrics_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)

        # Custom metrics table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS custom_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                formula TEXT NOT NULL,
                description TEXT,
                metric_type TEXT NOT NULL DEFAULT 'formula',
                config_json TEXT DEFAULT '{}',
                is_builtin BOOLEAN DEFAULT 0,
                is_editable BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.commit()
        await _migrate_schema(db)


async def _migrate_schema(db: aiosqlite.Connection) -> None:
    """Add columns introduced after initial schema."""
    cursor = await db.execute("PRAGMA table_info(custom_metrics)")
    metric_columns = {row[1] for row in await cursor.fetchall()}

    if "metric_type" not in metric_columns:
        await db.execute(
            "ALTER TABLE custom_metrics ADD COLUMN metric_type TEXT NOT NULL DEFAULT 'formula'"
        )
    if "config_json" not in metric_columns:
        await db.execute("ALTER TABLE custom_metrics ADD COLUMN config_json TEXT DEFAULT '{}'")
    if "is_editable" not in metric_columns:
        await db.execute("ALTER TABLE custom_metrics ADD COLUMN is_editable BOOLEAN DEFAULT 1")
    if "updated_at" not in metric_columns:
        await db.execute("ALTER TABLE custom_metrics ADD COLUMN updated_at TIMESTAMP")

    await db.commit()


async def get_db() -> aiosqlite.Connection:
    """Get database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


async def seed_builtin_rules() -> None:
    """Seed built-in rules from YAML files into the database."""
    from ca_engine.rules.yaml_loader import YAMLRuleLoader
    import yaml

    rules_dir = Path(__file__).resolve().parents[1] / "rules"
    loader = YAMLRuleLoader(rules_dir)

    async with aiosqlite.connect(DB_PATH) as db:
        for path in sorted(rules_dir.glob("*.yaml")):
            name = path.stem
            # Check if already exists
            cursor = await db.execute("SELECT id FROM rules WHERE name = ?", (name,))
            if await cursor.fetchone():
                continue

            with open(path) as f:
                data = yaml.safe_load(f)

            yaml_content = path.read_text()
            description = data.get("description", f"Built-in rule: {name}")
            category = data.get("category", "experimental")

            await db.execute(
                """INSERT INTO rules (name, yaml_content, is_builtin, is_editable, description, category)
                   VALUES (?, ?, 1, 0, ?, ?)""",
                (name, yaml_content, description, category),
            )
        await db.commit()


async def seed_builtin_metrics() -> None:
    """Seed built-in metrics into the database."""
    async with aiosqlite.connect(DB_PATH) as db:
        metrics = [
            ("density", "density", "Fraction of non-zero cells"),
            ("entropy", "entropy", "Shannon entropy over all states"),
            ("entropy_nonzero", "entropy_nonzero", "Shannon entropy excluding state 0"),
        ]
        for name, formula, desc in metrics:
            cursor = await db.execute("SELECT id FROM custom_metrics WHERE name = ?", (name,))
            if not await cursor.fetchone():
                await db.execute(
                    """INSERT INTO custom_metrics
                       (name, formula, description, metric_type, config_json, is_builtin, is_editable)
                       VALUES (?, ?, ?, ?, '{}', 1, 0)""",
                    (name, formula, desc, name),
                )
        await db.commit()
