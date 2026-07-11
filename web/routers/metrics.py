"""Metrics API routes."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException

from ca_engine.metrics.registry import MetricRegistry
from web.database import get_db
from web.models import MetricCreate, MetricOut, MetricUpdate, ValidationResult
from web.services.metric_loader import validate_metric_names
from web.services.metric_validation import (
    list_metric_templates,
    metric_row_to_out,
    validate_metric_payload,
)

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
            "id": None,
            "name": meta.name,
            "description": meta.description or "",
            "category": meta.category or "structure",
            "metric_type": meta.name,
            "formula": meta.name,
            "config": {},
            "is_builtin": True,
            "is_editable": False,
        })

    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, name, formula, description, metric_type, config_json,
                      is_builtin, is_editable, created_at
               FROM custom_metrics ORDER BY name"""
        )
        rows = await cursor.fetchall()
        for row in rows:
            d = metric_row_to_out(dict(row))
            name = d["name"]
            if name in seen:
                continue
            seen.add(name)
            result.append({
                **d,
                "category": "custom" if not d["is_builtin"] else "structure",
            })
    finally:
        await db.close()

    result.sort(key=lambda m: (not m["is_builtin"], m["name"]))
    return result


@router.get("/templates")
async def get_metric_templates() -> list[dict[str, Any]]:
    """List metric template types for the visual builder."""
    return list_metric_templates()


@router.get("/{metric_id}", response_model=MetricOut)
async def get_metric(metric_id: int) -> dict[str, Any]:
    """Get a single custom metric by ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, name, formula, description, metric_type, config_json,
                      is_builtin, is_editable, created_at
               FROM custom_metrics WHERE id = ?""",
            (metric_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Metric not found")
        return metric_row_to_out(dict(row))
    finally:
        await db.close()


@router.post("/", response_model=MetricOut)
async def create_metric(metric: MetricCreate) -> dict[str, Any]:
    """Create a new custom metric."""
    validation = validate_metric_payload(
        metric.name,
        metric.metric_type,
        metric.formula,
        metric.config,
        metric.description,
    )
    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail=validation.errors[0].get("message", "Invalid metric"),
        )

    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM custom_metrics WHERE LOWER(name) = LOWER(?)", (metric.name,))
        if await cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"Metric name '{metric.name}' already exists")

        stored_formula = metric.formula
        if metric.metric_type in ("state_count", "state_ratio", "alive_ratio") and not stored_formula:
            stored_formula = metric.metric_type

        cursor = await db.execute(
            """INSERT INTO custom_metrics
               (name, formula, description, metric_type, config_json, is_builtin, is_editable)
               VALUES (?, ?, ?, ?, ?, 0, 1)""",
            (
                metric.name,
                stored_formula,
                metric.description,
                metric.metric_type,
                json.dumps(metric.config),
            ),
        )
        await db.commit()
        return await get_metric(cursor.lastrowid)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await db.close()


@router.put("/{metric_id}", response_model=MetricOut)
async def update_metric(metric_id: int, metric: MetricUpdate) -> dict[str, Any]:
    """Update a custom metric."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, name, formula, description, metric_type, config_json,
                      is_builtin, is_editable
               FROM custom_metrics WHERE id = ?""",
            (metric_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Metric not found")
        if row["is_builtin"]:
            raise HTTPException(status_code=403, detail="Built-in metrics cannot be edited")

        current = dict(row)
        new_name = metric.name if metric.name is not None else current["name"]
        new_type = metric.metric_type if metric.metric_type is not None else current.get("metric_type", "formula")
        new_formula = metric.formula if metric.formula is not None else current.get("formula", "")
        config_raw = current.get("config_json") or "{}"
        current_config = json.loads(config_raw) if isinstance(config_raw, str) else config_raw
        new_config = metric.config if metric.config is not None else current_config
        new_desc = metric.description if metric.description is not None else current.get("description", "")

        if metric.name is not None:
            cursor = await db.execute(
                "SELECT id FROM custom_metrics WHERE LOWER(name) = LOWER(?) AND id != ?",
                (metric.name, metric_id),
            )
            if await cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Metric name '{metric.name}' already exists")

        validation = validate_metric_payload(new_name, new_type, new_formula, new_config, new_desc)
        if not validation.is_valid:
            raise HTTPException(
                status_code=400,
                detail=validation.errors[0].get("message", "Invalid metric"),
            )

        fields = []
        values: list[Any] = []
        if metric.name is not None:
            fields.append("name = ?")
            values.append(metric.name)
        if metric.metric_type is not None:
            fields.append("metric_type = ?")
            values.append(metric.metric_type)
        if metric.formula is not None:
            fields.append("formula = ?")
            values.append(metric.formula)
        if metric.config is not None:
            fields.append("config_json = ?")
            values.append(json.dumps(metric.config))
        if metric.description is not None:
            fields.append("description = ?")
            values.append(metric.description)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(metric_id)
        await db.execute(f"UPDATE custom_metrics SET {', '.join(fields)} WHERE id = ?", values)
        await db.commit()
        return await get_metric(metric_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await db.close()


@router.delete("/{metric_id}")
async def delete_metric(metric_id: int) -> dict[str, str]:
    """Delete a custom metric."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT name, is_builtin FROM custom_metrics WHERE id = ?",
            (metric_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Metric not found")
        if row["is_builtin"]:
            raise HTTPException(status_code=403, detail="Built-in metrics cannot be deleted")

        metric_name = row["name"]
        cursor = await db.execute("SELECT id, metrics_enabled FROM sessions")
        sessions = await cursor.fetchall()
        in_use = 0
        for s in sessions:
            enabled = json.loads(s["metrics_enabled"] or "[]")
            if metric_name in enabled:
                in_use += 1
        if in_use > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Metric is enabled on {in_use} session(s). Remove it from those sessions first.",
            )

        await db.execute("DELETE FROM custom_metrics WHERE id = ?", (metric_id,))
        await db.commit()
        return {"message": "Metric deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await db.close()


@router.post("/validate", response_model=ValidationResult)
async def validate_metric(metric: MetricCreate) -> ValidationResult:
    """Validate a metric definition without saving."""
    return validate_metric_payload(
        metric.name,
        metric.metric_type,
        metric.formula,
        metric.config,
        metric.description,
    )
