"""Kolmogorov complexity metric: LZ78-based compressibility of the grid."""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import Metric


class KolmogorovMetric(Metric):
    """LZ78 dictionary size / sequence length as a proxy for complexity."""

    def __init__(self) -> None:
        super().__init__()
        self._values: dict[str, float] = {}

    @property
    def name(self) -> str:
        return "kolmogorov"

    def on_init(self, grid_shape: tuple[int, int], num_states: int) -> None:
        self._values = {}

    def on_step(self, grid: np.ndarray, step_num: int) -> None:
        h, w = grid.shape
        seq_len = h * w
        if seq_len == 0:
            self._values = {k: 0.0 for k in _LINEARIZERS}
            return

        counts: dict[str, float] = {}

        for name, linearizer in _LINEARIZERS.items():
            seq = linearizer(grid)
            lz_size = _lz78_size(seq)
            counts[name] = round(lz_size / seq_len, 6)

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
        return self._values.get("horizontal", 0.0)


def _lz78_size(seq: np.ndarray) -> int:
    """LZ78 dictionary size for a sequence."""
    dictionary: dict[tuple[int, ...], int] = {}
    i = 0
    n = len(seq)
    while i < n:
        j = i + 1
        while j <= n and tuple(seq[i:j]) in dictionary:
            j += 1
        if j <= n:
            dictionary[tuple(seq[i:j])] = len(dictionary) + 1
        i = j
    return len(dictionary)


def _horizontal(grid: np.ndarray) -> np.ndarray:
    return grid.ravel()


def _vertical(grid: np.ndarray) -> np.ndarray:
    return grid.T.ravel()


def _spiral(grid: np.ndarray) -> np.ndarray:
    h, w = grid.shape
    result = []
    top, bottom = 0, h - 1
    left, right = 0, w - 1
    while top <= bottom and left <= right:
        for x in range(left, right + 1):
            result.append(grid[top, x])
        top += 1
        for y in range(top, bottom + 1):
            result.append(grid[y, right])
        right -= 1
        if top <= bottom:
            for x in range(right, left - 1, -1):
                result.append(grid[bottom, x])
            bottom -= 1
        if left <= right:
            for y in range(bottom, top - 1, -1):
                result.append(grid[y, left])
            left += 1
    return np.array(result, dtype=grid.dtype)


def _diagonal(grid: np.ndarray) -> np.ndarray:
    h, w = grid.shape
    result = []
    for s in range(h + w - 1):
        if s < w:
            x, y = s, 0
        else:
            x, y = w - 1, s - w + 1
        while x >= 0 and y < h:
            result.append(grid[y, x])
            x -= 1
            y += 1
    return np.array(result, dtype=grid.dtype)


_LINEARIZERS = {
    "horizontal": _horizontal,
    "vertical": _vertical,
    "spiral": _spiral,
    "diagonal": _diagonal,
}
