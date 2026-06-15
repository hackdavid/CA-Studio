"""Metrics API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from web.database import get_db
from ca_engine.metrics.registry import MetricRegistry

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/")
async def list_metrics() -> list[dict[str, Any]]:
    """List all available metrics (built-in registry + custom DB entries)."""
    registry = MetricRegistry()
    seen: set[str] = set()
    result: list[dict[str, Any]] = []

    for meta in registry.list():
        seen.add(meta.name)
        result.append({
            "name": meta.name,
            "description": meta.description or "",
            "category": meta.category or "structure",
            "is_builtin": True,
        })

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT name, formula, description, is_builtin FROM custom_metrics ORDER BY name"
        )
        rows = await cursor.fetchall()
        for row in rows:
            name = row["name"]
            if name in seen:
                continue
            seen.add(name)
            result.append({
                "name": name,
                "description": row["description"] or "",
                "category": "custom",
                "is_builtin": bool(row["is_builtin"]),
            })
    finally:
        await db.close()

    result.sort(key=lambda m: (not m["is_builtin"], m["name"]))
    return result
