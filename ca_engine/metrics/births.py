"""Births metric: count of cells transitioning from 0 to non-zero per step."""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import Metric


class BirthsMetric(Metric):
    """Count cells that go from dead (0) to alive (non-zero) each step."""

    def __init__(self) -> None:
        super().__init__()
        self._births = 0
        self._next_births = 0

    @property
    def name(self) -> str:
        return "births"

    def on_init(self, grid_shape: tuple[int, int], num_states: int) -> None:
        self._births = 0
        self._next_births = 0

    def on_step(self, grid: np.ndarray, step_num: int) -> None:
        self._births = self._next_births
        self._next_births = 0

    def on_cell_update(self, old: int, new: int, x: int, y: int) -> None:
        if old == 0 and new != 0:
            self._next_births += 1

    def reset(self) -> None:
        self._births = 0
        self._next_births = 0

    @property
    def values(self) -> dict[str, Any]:
        return {self.name: self._births}

    @property
    def value(self) -> float:
        return float(self._births)
