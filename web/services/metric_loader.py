"""Load custom metrics from database for simulation runtime."""

from __future__ import annotations

from typing import Any

from web.database import get_db


async def fetch_custom_metric_by_name(name: str) -> dict[str, Any] | None:
    """Load a custom metric row by name."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, name, formula, description, metric_type, config_json,
                      is_builtin, is_editable, created_at
               FROM custom_metrics WHERE name = ?""",
            (name,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def fetch_all_custom_metrics() -> dict[str, dict[str, Any]]:
    """Load all custom metrics keyed by name."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, name, formula, description, metric_type, config_json,
                      is_builtin, is_editable, created_at
               FROM custom_metrics"""
        )
        rows = await cursor.fetchall()
        return {row["name"]: dict(row) for row in rows}
    finally:
        await db.close()


async def metric_name_exists(name: str) -> bool:
    """Check if metric exists in registry or custom_metrics table."""
    from ca_engine.metrics.registry import MetricRegistry

    if name in MetricRegistry():
        return True
    row = await fetch_custom_metric_by_name(name)
    return row is not None


async def validate_metric_names(names: list[str]) -> list[str]:
    """Return list of metric names that cannot be resolved."""
    from ca_engine.metrics.registry import MetricRegistry

    registry = MetricRegistry()
    invalid: list[str] = []
    custom_cache: dict[str, dict[str, Any] | None] = {}

    for name in names:
        if name in registry:
            continue
        if name not in custom_cache:
            custom_cache[name] = await fetch_custom_metric_by_name(name)
        if custom_cache[name] is None:
            invalid.append(name)
    return invalid
