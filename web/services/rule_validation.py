"""Shared rule validation for API create/update/validate endpoints."""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import yaml

from ca_engine.core.board import Board
from ca_engine.core.neighbourhood import Neighbourhood
from ca_engine.core.palette import Palette
from ca_engine.core.simulator import Simulator
from ca_engine.rules.compiler import rule_table_to_rows
from ca_engine.rules.validator import RuleValidator
from ca_engine.rules.yaml_loader import YAMLRuleLoader
from web.models import ValidationResult

VALID_NEIGHBOURHOODS = frozenset({"moore8", "moore9", "neumann", "neumann_center"})
RULE_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,31}$")


def _to_api_result(engine_result: Any) -> ValidationResult:
    """Convert engine ValidationResult to API ValidationResult."""
    errors = [
        {
            "line": e.line,
            "message": e.message,
            "got": e.got,
            "expected": e.expected,
        }
        for e in engine_result.errors
    ]
    warnings = [{"line": w.line, "message": w.message} for w in engine_result.warnings]
    return ValidationResult(
        is_valid=engine_result.is_valid,
        errors=errors,
        warnings=warnings,
    )


def validate_rule_name(name: str) -> list[dict[str, Any]]:
    """Validate rule name format."""
    if not name or not RULE_NAME_PATTERN.match(name):
        return [
            {
                "line": None,
                "message": "Name must be 3-32 characters, start with a letter, and use only letters, numbers, or underscores",
                "got": name,
                "expected": "e.g. MyRule_01",
            }
        ]
    return []


def validate_rule_yaml(yaml_content: str, rule_name: str | None = None) -> ValidationResult:
    """Parse YAML, run RuleValidator, and optional dry-run simulation."""
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        return ValidationResult(
            is_valid=False,
            errors=[{"line": None, "message": f"Invalid YAML: {e}"}],
            warnings=[],
        )

    if not isinstance(data, dict):
        return ValidationResult(
            is_valid=False,
            errors=[{"line": None, "message": "Rule YAML must be a mapping/object"}],
            warnings=[],
        )

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    num_states = data.get("states", data.get("num_states", 101))
    if not isinstance(num_states, int) or num_states < 2 or num_states > 101:
        errors.append(
            {
                "line": None,
                "message": "states must be an integer between 2 and 101",
                "got": str(num_states),
                "expected": "2..101",
            }
        )

    neighbourhood = data.get("neighbourhood", "moore8")
    if neighbourhood not in VALID_NEIGHBOURHOODS:
        errors.append(
            {
                "line": None,
                "message": f"Invalid neighbourhood '{neighbourhood}'",
                "got": str(neighbourhood),
                "expected": ", ".join(sorted(VALID_NEIGHBOURHOODS)),
            }
        )

    transitions = data.get("transitions", data.get("rows", []))
    if not transitions:
        errors.append({"line": None, "message": "Rule must have at least one transition"})

    if rule_name:
        errors.extend(validate_rule_name(rule_name))

    if errors:
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    try:
        loader = YAMLRuleLoader()
        table = loader._parse(data)
        rows = rule_table_to_rows(table.table, table.num_states)
        validator = RuleValidator(num_states=table.num_states)
        engine_result = validator.validate(rows)
        api_result = _to_api_result(engine_result)
        warnings.extend(api_result.warnings)

        dry_run_warning = _dry_run_static_rule(table, num_states, neighbourhood)
        if dry_run_warning:
            warnings.append({"line": None, "message": dry_run_warning})

        return ValidationResult(
            is_valid=api_result.is_valid,
            errors=api_result.errors,
            warnings=warnings,
        )
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            errors=[{"line": None, "message": str(e)}],
            warnings=warnings,
        )


def _dry_run_static_rule(table: Any, num_states: int, neighbourhood: str) -> str | None:
    """Run a short simulation; warn if grid never changes."""
    try:
        board = Board(5, 5)
        board.data[2, 2] = 1
        neighbourhood_obj = Neighbourhood.from_name(neighbourhood)
        palette = Palette.default(num_states)
        sim = Simulator(board, table, neighbourhood_obj, palette)
        initial = sim.board.data.copy()
        for _ in range(10):
            sim.step()
        if np.array_equal(sim.board.data, initial):
            return "Dry-run: grid did not change after 10 steps on a small test pattern"
    except Exception:
        pass
    return None


def build_yaml_from_metadata(
    name: str,
    description: str,
    category: str,
    states: int,
    neighbourhood: str,
    transitions: list[dict[str, Any]],
) -> str:
    """Build canonical YAML from visual builder payload."""
    data: dict[str, Any] = {
        "name": name,
        "version": "1.0",
        "states": states,
        "neighbourhood": neighbourhood,
        "description": description,
        "category": category,
        "transitions": transitions,
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False)
