"""Tests for metric formula DSL and validation."""

import numpy as np
import pytest

from ca_engine.metrics.dynamic import DynamicMetricFactory, FormulaMetric, StateCountMetric
from ca_engine.metrics.formula import SafeFormulaEvaluator, validate_metric_name
from web.services.metric_validation import validate_metric_payload


def test_safe_formula_valid():
    ev = SafeFormulaEvaluator()
    assert ev.validate("density * 100") == []
    val = ev.evaluate("density * 100", {"density": 0.5, "entropy": 1.0, "entropy_nonzero": 0.8})
    assert val == 50.0


def test_safe_formula_rejects_unknown():
    ev = SafeFormulaEvaluator()
    errors = ev.validate("foo + 1")
    assert errors


def test_safe_formula_rejects_call():
    ev = SafeFormulaEvaluator()
    errors = ev.validate("__import__('os')")
    assert errors


def test_metric_name_reserved():
    assert validate_metric_name("density")


def test_validate_state_count_metric():
    result = validate_metric_payload("cells_in_state_1", "state_count", "", {"state": 1})
    assert result.is_valid


def test_validate_formula_metric():
    result = validate_metric_payload("combo", "formula", "density + entropy", {})
    assert result.is_valid


def test_state_count_metric_runtime():
    m = StateCountMetric("cells_in_state_1", 1)
    m.on_init((4, 4), 2)
    grid = np.zeros((4, 4), dtype=np.uint8)
    grid[0, 0] = 1
    grid[1, 1] = 1
    m.on_step(grid, 1)
    assert m.values["cells_in_state_1"] == 2


def test_formula_metric_runtime():
    m = FormulaMetric("pct_alive", "density * 100")
    m.on_init((4, 4), 2)
    grid = np.zeros((4, 4), dtype=np.uint8)
    grid[0, 0] = 1
    m.on_step(grid, 1)
    assert m.values["pct_alive"] == pytest.approx(6.25)


def test_dynamic_factory_from_row():
    row = {
        "name": "my_count",
        "metric_type": "state_count",
        "formula": "state_count",
        "config_json": '{"state": 1}',
    }
    metric = DynamicMetricFactory.from_db_row(row)
    assert metric.name == "my_count"
