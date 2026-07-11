"""Shannon entropy metric: H = -sum(p_i * log2(p_i))."""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import Metric


class EntropyMetric(Metric):
    """Shannon entropy over all states.

    H = -sum(p_i * log2(p_i)) where p_i is the fraction of cells in state i.
    """

    def __init__(self, exclude_zero: bool = False) -> None:
        super().__init__()
        self._exclude_zero = exclude_zero
        self._entropy = 0.0
        self._num_states = 0

    @property
    def name(self) -> str:
        return "entropy" if not self._exclude_zero else "entropy_nonzero"

    def on_init(self, grid_shape: tuple[int, int], num_states: int) -> None:
        self._num_states = num_states
        self._entropy = 0.0

    def on_step(self, grid: np.ndarray, step_num: int) -> None:
        self._entropy = self._compute(grid)

    def _compute(self, grid: np.ndarray) -> float:
        total = grid.size
        if total == 0:
            return 0.0

        # Count each state — use actual max to avoid out-of-bounds
        actual_max = int(grid.max()) + 1
        counts = np.bincount(grid.ravel(), minlength=max(self._num_states, actual_max))

        if self._exclude_zero:
            counts = counts[1:]
            total = counts.sum()

        if total == 0:
            return 0.0

        probs = counts / total
        # Only non-zero probabilities contribute
        nonzero_probs = probs[probs > 0]
        if len(nonzero_probs) == 0:
            return 0.0

        entropy = -np.sum(nonzero_probs * np.log2(nonzero_probs))
        return float(entropy)

    def reset(self) -> None:
        self._entropy = 0.0

    @property
    def values(self) -> dict[str, Any]:
        return {self.name: self._entropy}

    @property
    def value(self) -> float:
        return self._entropy
