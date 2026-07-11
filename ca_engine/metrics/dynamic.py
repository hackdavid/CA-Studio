"""Dynamic metric classes for DB-defined custom metrics."""

from __future__ import annotations

import json
from typing import Any

import numpy as np

from .base import Metric
from .formula import SafeFormulaEvaluator, compute_builtin_context
from .registry import MetricRegistry


class StateCountMetric(Metric):
    """Count cells in a specific state."""

    def __init__(self, metric_name: str, state: int) -> None:
        super().__init__()
        self._metric_name = metric_name
        self._state = state
        self._count = 0

    @property
    def name(self) -> str:
        return self._metric_name

    def on_init(self, grid_shape: tuple[int, int], num_states: int) -> None:
        self._count = 0

    def on_step(self, grid: np.ndarray, step_num: int) -> None:
        self._count = int(np.sum(grid == self._state))

    def reset(self) -> None:
        self._count = 0

    @property
    def values(self) -> dict[str, Any]:
        return {self.name: self._count}


class StateRatioMetric(Metric):
    """Fraction of cells in a specific state."""

    def __init__(self, metric_name: str, state: int) -> None:
        super().__init__()
        self._metric_name = metric_name
        self._state = state
        self._ratio = 0.0
        self._total = 0

    @property
    def name(self) -> str:
        return self._metric_name

    def on_init(self, grid_shape: tuple[int, int], num_states: int) -> None:
        self._total = grid_shape[0] * grid_shape[1]
        self._ratio = 0.0

    def on_step(self, grid: np.ndarray, step_num: int) -> None:
        if self._total == 0:
            self._ratio = 0.0
        else:
            self._ratio = float(np.sum(grid == self._state)) / self._total

    def reset(self) -> None:
        self._ratio = 0.0

    @property
    def values(self) -> dict[str, Any]:
        return {self.name: self._ratio}


class AliveRatioMetric(Metric):
    """Fraction of non-zero cells (same as density, custom name)."""

    def __init__(self, metric_name: str) -> None:
        super().__init__()
        self._metric_name = metric_name
        self._ratio = 0.0
        self._total = 0

    @property
    def name(self) -> str:
        return self._metric_name

    def on_init(self, grid_shape: tuple[int, int], num_states: int) -> None:
        self._total = grid_shape[0] * grid_shape[1]
        self._ratio = 0.0

    def on_step(self, grid: np.ndarray, step_num: int) -> None:
        if self._total == 0:
            self._ratio = 0.0
        else:
            self._ratio = float(np.count_nonzero(grid)) / self._total

    def reset(self) -> None:
        self._ratio = 0.0

    @property
    def values(self) -> dict[str, Any]:
        return {self.name: self._ratio}


class FormulaMetric(Metric):
    """Metric defined by a safe arithmetic formula over builtins."""

    def __init__(self, metric_name: str, formula: str) -> None:
        super().__init__()
        self._metric_name = metric_name
        self._formula = formula
        self._value = 0.0
        self._num_states = 2
        self._evaluator = SafeFormulaEvaluator()

    @property
    def name(self) -> str:
        return self._metric_name

    def on_init(self, grid_shape: tuple[int, int], num_states: int) -> None:
        self._num_states = num_states
        self._value = 0.0

    def on_step(self, grid: np.ndarray, step_num: int) -> None:
        context = compute_builtin_context(grid, self._num_states)
        self._value = self._evaluator.evaluate(self._formula, context)

    def reset(self) -> None:
        self._value = 0.0

    @property
    def values(self) -> dict[str, Any]:
        return {self.name: self._value}


class DynamicMetricFactory:
    """Create Metric instances from database rows."""

    @staticmethod
    def from_db_row(row: dict[str, Any]) -> Metric:
        name = row["name"]
        metric_type = row.get("metric_type") or "formula"
        config = row.get("config_json") or {}
        if isinstance(config, str):
            config = json.loads(config or "{}")

        if metric_type == "state_count":
            state = int(config.get("state", 0))
            return StateCountMetric(name, state)
        if metric_type == "state_ratio":
            state = int(config.get("state", 0))
            return StateRatioMetric(name, state)
        if metric_type == "alive_ratio":
            return AliveRatioMetric(name)
        if metric_type == "formula":
            formula = row.get("formula") or ""
            return FormulaMetric(name, formula)

        raise ValueError(f"Unknown metric type: {metric_type}")

    @staticmethod
    def resolve_metric(
        name: str,
        registry: MetricRegistry,
        custom_row: dict[str, Any] | None,
    ) -> Metric:
        """Resolve builtin or custom metric by name."""
        if name in registry:
            return registry.get(name)
        if custom_row is not None:
            return DynamicMetricFactory.from_db_row(custom_row)
        raise KeyError(f"Metric '{name}' not found")
