"""Deaths metric: count of cells transitioning from non-zero to 0 per step."""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import Metric


class DeathsMetric(Metric):
    """Count cells that go from alive (non-zero) to dead (0) each step."""

    def __init__(self) -> None:
        super().__init__()
        self._deaths = 0
        self._next_deaths = 0

    @property
    def name(self) -> str:
        return "deaths"

    def on_init(self, grid_shape: tuple[int, int], num_states: int) -> None:
        self._deaths = 0
        self._next_deaths = 0

    def on_step(self, grid: np.ndarray, step_num: int) -> None:
        self._deaths = self._next_deaths
        self._next_deaths = 0

    def on_cell_update(self, old: int, new: int, x: int, y: int) -> None:
        if old != 0 and new == 0:
            self._next_deaths += 1

    def reset(self) -> None:
        self._deaths = 0
        self._next_deaths = 0

    @property
    def values(self) -> dict[str, Any]:
        return {self.name: self._deaths}

    @property
    def value(self) -> float:
        return float(self._deaths)
