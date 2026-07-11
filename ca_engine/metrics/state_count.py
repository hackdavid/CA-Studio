"""State count metric: number of distinct states currently present."""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import Metric


class StateCountMetric(Metric):
    """Number of distinct non-zero states on the board."""

    def __init__(self) -> None:
        super().__init__()
        self._state_count = 0

    @property
    def name(self) -> str:
        return "state_count"

    def on_init(self, grid_shape: tuple[int, int], num_states: int) -> None:
        self._state_count = 0

    def on_step(self, grid: np.ndarray, step_num: int) -> None:
        uniques = np.unique(grid)
        # Count non-zero states only
        self._state_count = int(np.count_nonzero(uniques != 0))

    def on_cell_update(self, old: int, new: int, x: int, y: int) -> None:
        pass

    def reset(self) -> None:
        self._state_count = 0

    @property
    def values(self) -> dict[str, Any]:
        return {self.name: self._state_count}

    @property
    def value(self) -> float:
        return float(self._state_count)
