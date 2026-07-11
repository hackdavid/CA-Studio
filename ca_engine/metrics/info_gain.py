"""Information gain (mutual information) metric between a cell and its 4 neighbors."""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import Metric


class InfoGainMetric(Metric):
    """Mutual information I(X;Y) between a cell and its neighbor in 4 directions."""

    def __init__(self) -> None:
        super().__init__()
        self._num_states = 2
        self._values: dict[str, float] = {}

    @property
    def name(self) -> str:
        return "info_gain"

    def on_init(self, grid_shape: tuple[int, int], num_states: int) -> None:
        self._num_states = max(2, num_states)
        self._values = {}

    def on_step(self, grid: np.ndarray, step_num: int) -> None:
        h, w = grid.shape
        if h < 2 or w < 2:
            self._values = {k: 0.0 for k in _DIRECTIONS}
            return

        # Use actual max state in grid + 1 to avoid out-of-bounds
        actual_states = max(self._num_states, int(grid.max()) + 1)

        directions = {
            "up": ((-1, 0), (0, h - 1), (0, w)),
            "down": ((1, 0), (0, h - 1), (0, w)),
            "left": ((0, -1), (0, h), (0, w - 1)),
            "right": ((0, 1), (0, h), (0, w - 1)),
        }

        counts: dict[str, float] = {}
        total = float(h * w)

        for name, ((dy, dx), yr, xr) in directions.items():
            joint = np.zeros((actual_states, actual_states), dtype=np.float64)
            for y in range(yr[0], yr[1]):
                for x in range(xr[0], xr[1]):
                    ny = y + dy
                    nx = x + dx
                    a = int(grid[y, x])
                    b = int(grid[ny, nx])
                    joint[a, b] += 1

            joint /= total
            marginal_a = joint.sum(axis=1)
            marginal_b = joint.sum(axis=0)

            mi = 0.0
            for a in range(actual_states):
                for b in range(actual_states):
                    p_xy = joint[a, b]
                    if p_xy > 0 and marginal_a[a] > 0 and marginal_b[b] > 0:
                        mi += p_xy * np.log2(p_xy / (marginal_a[a] * marginal_b[b]))
            counts[name] = round(float(mi), 6)

        self._values = counts

    def on_cell_update(self, old: int, new: int, x: int, y: int) -> None:
        pass

    def reset(self) -> None:
        self._values = {}

    @property
    def values(self) -> dict[str, Any]:
        return dict(self._values)

    @property
    def value(self) -> float:
        return self._values.get("right", 0.0)


_DIRECTIONS = ["up", "down", "left", "right"]
