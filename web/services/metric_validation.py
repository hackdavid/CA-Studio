"""Shared metric validation for API create/update/validate endpoints."""

from __future__ import annotations

import json
from typing import Any

from ca_engine.metrics.formula import (
    SafeFormulaEvaluator,
    build_test_grid,
    compute_builtin_context,
    validate_metric_name,
)
from ca_engine.metrics.registry import MetricRegistry
from web.models import ValidationResult

METRIC_TEMPLATES = [
    {
        "type": "state_count",
        "title": "Count cells in a state",
        "description": "How many cells are currently in a chosen state?",
        "fields": [{"name": "state", "type": "integer", "label": "State number", "min": 0, "max": 100}],
    },
    {
        "type": "state_ratio",
        "title": "Fraction of cells in a state",
        "description": "What share of the board is in a chosen state (0 to 1)?",
        "fields": [{"name": "state", "type": "integer", "label": "State number", "min": 0, "max": 100}],
    },
    {
        "type": "alive_ratio",
        "title": "Alive cell fraction",
        "description": "Fraction of cells that are not empty (state 0).",
        "fields": [],
    },
    {
        "type": "formula",
        "title": "Combine measurements",
        "description": "Build a formula from density, entropy, and arithmetic operators.",
        "fields": [
            {
                "name": "formula",
                "type": "string",
                "label": "Formula",
                "examples": ["density * 100", "(entropy + density) / 2"],
            }
        ],
        "allowed_identifiers": sorted(SafeFormulaEvaluator().allowed_names),
    },
]

RESERVED_NAMES = frozenset(MetricRegistry().names())


def list_metric_templates() -> list[dict[str, Any]]:
    return METRIC_TEMPLATES


def validate_metric_payload(
    name: str,
    metric_type: str,
    formula: str,
    config: dict[str, Any],
    description: str = "",
) -> ValidationResult:
    """Validate a custom metric definition."""
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for msg in validate_metric_name(name):
        errors.append({"line": None, "message": msg})

    valid_types = {t["type"] for t in METRIC_TEMPLATES}
    if metric_type not in valid_types:
        errors.append(
            {
                "line": None,
                "message": f"Invalid metric_type '{metric_type}'",
                "expected": ", ".join(sorted(valid_types)),
            }
        )

    if metric_type in ("state_count", "state_ratio"):
        if "state" not in config:
            errors.append({"line": None, "message": "config.state is required"})
        else:
            state = config["state"]
            if not isinstance(state, int) or state < 0 or state >= 101:
                errors.append(
                    {
                        "line": None,
                        "message": "state must be an integer from 0 to 100",
                        "got": str(state),
                    }
                )
            elif state > 10:
                warnings.append(
                    {"line": None, "message": f"State {state} is unusually high for typical CA experiments"}
                )

    if metric_type == "alive_ratio":
        if name in RESERVED_NAMES:
            pass  # already caught by validate_metric_name

    if metric_type == "formula":
        evaluator = SafeFormulaEvaluator()
        for msg in evaluator.validate(formula):
            errors.append({"line": None, "message": msg})

        if not errors:
            grid = build_test_grid()
            context = compute_builtin_context(grid, num_states=4)
            try:
                v1 = evaluator.evaluate(formula, context)
                grid2 = build_test_grid(shape=(8, 8), num_states=4)
                grid2[0, :] = 1
                context2 = compute_builtin_context(grid2, num_states=4)
                v2 = evaluator.evaluate(formula, context2)
                if v1 == v2:
                    warnings.append(
                        {
                            "line": None,
                            "message": "Formula returns the same value on different test grids; check for typos",
                        }
                    )
            except Exception as e:
                errors.append({"line": None, "message": f"Test evaluation failed: {e}"})

    if not description.strip() and metric_type != "formula":
        warnings.append({"line": None, "message": "Adding a description helps when selecting metrics later"})

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def metric_row_to_out(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize DB row for API response."""
    config_raw = row.get("config_json") or "{}"
    if isinstance(config_raw, str):
        config = json.loads(config_raw)
    else:
        config = config_raw
    return {
        "id": row["id"],
        "name": row["name"],
        "formula": row.get("formula") or "",
        "description": row.get("description") or "",
        "metric_type": row.get("metric_type") or "formula",
        "config": config,
        "is_builtin": bool(row.get("is_builtin")),
        "is_editable": bool(row.get("is_editable", True)),
        "created_at": str(row.get("created_at") or ""),
    }
