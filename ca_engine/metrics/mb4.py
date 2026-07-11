"""Normalized entropy (MB4) metric: H / Hmax where Hmax = log2(num_states)."""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import Metric


class NormalizedEntropyMetric(Metric):
    """Entropy normalized to [0,1] by dividing by the theoretical maximum."""

    def __init__(self) -> None:
        super().__init__()
        self._num_states = 2
        self._entropy_norm = 0.0

    @property
    def name(self) -> str:
        return "normalized_entropy"

    def on_init(self, grid_shape: tuple[int, int], num_states: int) -> None:
        self._num_states = max(2, num_states)
        self._entropy_norm = 0.0

    def on_step(self, grid: np.ndarray, step_num: int) -> None:
        flat = grid.ravel()
        total = flat.size
        if total == 0:
            self._entropy_norm = 0.0
            return
        actual_max = int(grid.max()) + 1
        counts = np.bincount(flat, minlength=max(self._num_states, actual_max))
        probs = counts / total
        probs = probs[probs > 0]
        entropy = float(-np.sum(probs * np.log2(probs)))
        h_max = np.log2(max(self._num_states, actual_max))
        self._entropy_norm = entropy / h_max if h_max > 0 else 0.0

    def on_cell_update(self, old: int, new: int, x: int, y: int) -> None:
        pass

    def reset(self) -> None:
        self._entropy_norm = 0.0

    @property
    def values(self) -> dict[str, Any]:
        return {"normalized_entropy": round(self._entropy_norm, 6)}

    @property
    def value(self) -> float:
        return self._entropy_norm
