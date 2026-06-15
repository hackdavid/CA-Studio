"""Density metric: fraction of non-zero cells."""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import Metric


class DensityMetric(Metric):
    """Fraction of cells with state != 0.

    Updated incrementally for performance.
    """

    def __init__(self) -> None:
        super().__init__()
        self._count = 0
        self._total = 0

    @property
    def name(self) -> str:
        return "density"

    def on_init(self, grid_shape: tuple[int, int], num_states: int) -> None:
        self._total = grid_shape[0] * grid_shape[1]
        self._count = 0

    def on_step(self, grid: np.ndarray, step_num: int) -> None:
        self._count = np.count_nonzero(grid)

    def on_cell_update(self, old: int, new: int, x: int, y: int) -> None:
        if old != 0:
            self._count -= 1
        if new != 0:
            self._count += 1

    def reset(self) -> None:
        self._count = 0

    @property
    def values(self) -> dict[str, Any]:
        if self._total == 0:
            return {self.name: 0.0}
        return {self.name: float(self._count) / self._total}

    @property
    def value(self) -> float:
        return self.values[self.name]
