"""Ratio metric: configurable ratio of selected states."""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import Metric


class RatioMetric(Metric):
    """Ratio of numerator states to denominator states (both must be non-empty)."""

    def __init__(
        self,
        numerator: list[int] | None = None,
        denominator: list[int] | None = None,
    ) -> None:
        super().__init__()
        self._numerator = set(numerator) if numerator else {1}
        self._denominator = set(denominator) if denominator else {2}
        self._ratio = 0.0

    @property
    def name(self) -> str:
        return "ratio"

    def on_init(self, grid_shape: tuple[int, int], num_states: int) -> None:
        self._ratio = 0.0

    def on_step(self, grid: np.ndarray, step_num: int) -> None:
        flat = grid.ravel()
        num_count = sum(1 for v in flat if int(v) in self._numerator)
        den_count = sum(1 for v in flat if int(v) in self._denominator)
        if den_count == 0:
            self._ratio = float("inf") if num_count > 0 else 0.0
        else:
            self._ratio = num_count / den_count

    def on_cell_update(self, old: int, new: int, x: int, y: int) -> None:
        pass

    def reset(self) -> None:
        self._ratio = 0.0

    @property
    def values(self) -> dict[str, Any]:
        return {
            "ratio": round(self._ratio, 6) if self._ratio != float("inf") else None,
            "numerator_states": sorted(self._numerator),
            "denominator_states": sorted(self._denominator),
        }

    @property
    def value(self) -> float:
        return self._ratio if self._ratio != float("inf") else 0.0
