"""Neighbourhood definitions and vectorized live-neighbour counting."""

from __future__ import annotations

from enum import Enum
from typing import Any, TYPE_CHECKING

import numpy as np
from scipy.signal import convolve2d

if TYPE_CHECKING:
    from .grid import Grid


class Neighbourhood(Enum):
    """Neighbourhood templates for live-neighbour counting.

    Live neighbours are cells with state > 0.
    """

    N4 = "n4"  # Von Neumann: up, down, left, right
    N5 = "n5"  # N4 + center
    N8 = "n8"  # Moore: all 8 surrounding
    N9 = "n9"  # Moore + center

    def __init__(self, value: str) -> None:
        self._value = value
        self._kernel = self._make_kernel()

    def _make_kernel(self) -> np.ndarray:
        """Build a convolution kernel for this neighbourhood.

        The kernel is 3x3 where each cell is 1 if it counts as a neighbour,
        0 otherwise. Center cell is included only for N5/N9.
        """
        if self.name == "N4":
            return np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=np.uint8)
        elif self.name == "N5":
            return np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8)
        elif self.name == "N8":
            return np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.uint8)
        elif self.name == "N9":
            return np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]], dtype=np.uint8)
        else:
            raise ValueError(f"Unknown neighbourhood: {self}")

    @property
    def kernel(self) -> np.ndarray:
        return self._kernel

    @property
    def size(self) -> int:
        """Number of cells included in this neighbourhood."""
        return int(self._kernel.sum())

    def count(self, grid: Any) -> np.ndarray:
        """Count live neighbours for every cell.

        Args:
            grid: Either a Grid instance or a 2D numpy array of state indices.

        Returns:
            Array of shape (H, W) with neighbour counts 0..size.
        """
        # Duck-typing to avoid circular import at module level
        if hasattr(grid, "data"):
            data = grid.data
        else:
            data = grid

        # Live cells: state > 0
        live = (data > 0).astype(np.uint8)

        # Convolve with toroidal boundaries
        counts = convolve2d(live, self._kernel, mode="same", boundary="wrap")
        return counts.astype(np.uint8)

    @classmethod
    def from_name(cls, name: str) -> Neighbourhood:
        """Look up by string name (case-insensitive)."""
        mapping = {
            "n4": cls.N4,
            "von_neumann": cls.N4,
            "neumann": cls.N4,
            "n5": cls.N5,
            "von_neumann_center": cls.N5,
            "n8": cls.N8,
            "moore": cls.N8,
            "moore8": cls.N8,
            "n9": cls.N9,
            "moore_center": cls.N9,
            "moore9": cls.N9,
        }
        key = name.strip().lower()
        if key not in mapping:
            raise ValueError(f"Unknown neighbourhood: {name!r}. Known: {list(mapping.keys())}")
        return mapping[key]

    def __repr__(self) -> str:
        return f"Neighbourhood.{self.name}"


# Convenience aliases
N4 = Neighbourhood.N4
N5 = Neighbourhood.N5
N8 = Neighbourhood.N8
N9 = Neighbourhood.N9
