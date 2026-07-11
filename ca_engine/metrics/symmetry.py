"""Symmetry metric: fraction of cell pairs matching under various transforms."""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import Metric


class SymmetryMetric(Metric):
    """Measure 6 symmetry types: horizontal, vertical, diagonal, anti-diagonal, 180°, 90°."""

    def __init__(self) -> None:
        super().__init__()
        self._values: dict[str, float] = {}

    @property
    def name(self) -> str:
        return "symmetry"

    def on_init(self, grid_shape: tuple[int, int], num_states: int) -> None:
        self._values = {}

    def on_step(self, grid: np.ndarray, step_num: int) -> None:
        h, w = grid.shape
        if h == 0 or w == 0:
            self._values = {k: 0.0 for k in _SYMMETRY_KEYS}
            return

        counts: dict[str, float] = {}

        # Horizontal (mirror across vertical center line)
        match = 0
        pairs = 0
        for y in range(h):
            for x in range(w // 2):
                pairs += 1
                if grid[y, x] == grid[y, w - 1 - x]:
                    match += 1
        counts["horizontal"] = match / pairs if pairs else 0.0

        # Vertical (mirror across horizontal center line)
        match = 0
        pairs = 0
        for y in range(h // 2):
            for x in range(w):
                pairs += 1
                if grid[y, x] == grid[h - 1 - y, x]:
                    match += 1
        counts["vertical"] = match / pairs if pairs else 0.0

        # Diagonal (transpose)
        match = 0
        pairs = 0
        min_dim = min(h, w)
        for y in range(min_dim):
            for x in range(y + 1, min_dim):
                pairs += 1
                if grid[y, x] == grid[x, y]:
                    match += 1
        counts["diagonal"] = match / pairs if pairs else 0.0

        # Anti-diagonal (reverse transpose)
        match = 0
        pairs = 0
        for y in range(min_dim):
            for x in range(min_dim - y - 1):
                pairs += 1
                if grid[y, x] == grid[min_dim - 1 - x, min_dim - 1 - y]:
                    match += 1
        counts["anti_diagonal"] = match / pairs if pairs else 0.0

        # 180° rotation
        match = 0
        pairs = 0
        for y in range(h):
            for x in range(w):
                ry = h - 1 - y
                rx = w - 1 - x
                if (y, x) < (ry, rx):
                    pairs += 1
                    if grid[y, x] == grid[ry, rx]:
                        match += 1
        counts["rotation_180"] = match / pairs if pairs else 0.0

        # 90° rotation (only for square grids)
        if h == w:
            match = 0
            pairs = 0
            n = h
            for y in range(n):
                for x in range(n):
                    ry = n - 1 - x
                    rx = y
                    if (y, x) < (ry, rx):
                        pairs += 1
                        if grid[y, x] == grid[ry, rx]:
                            match += 1
            counts["rotation_90"] = match / pairs if pairs else 0.0
        else:
            counts["rotation_90"] = 0.0

        self._values = {k: round(v, 6) for k, v in counts.items()}

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


_SYMMETRY_KEYS = [
    "horizontal",
    "vertical",
    "diagonal",
    "anti_diagonal",
    "rotation_180",
    "rotation_90",
]
