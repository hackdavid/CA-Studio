"""Toroidal grid storage for cellular automaton state."""

from __future__ import annotations

import numpy as np


class Grid:
    """A toroidal grid of uint8 cell states.

    The grid stores state indices (0 .. K-1) in a NumPy array of shape (H, W).
    Coordinate system: (y, x) with origin at top-left.
    Boundaries wrap toroidally via modular arithmetic.
    """

    def __init__(self, width: int, height: int, dtype: np.dtype = np.uint8) -> None:
        self._width = width
        self._height = height
        self._dtype = dtype
        self._data = np.zeros((height, width), dtype=dtype)

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def shape(self) -> tuple[int, int]:
        return (self._height, self._width)

    @property
    def data(self) -> np.ndarray:
        """Direct access to the underlying NumPy array."""
        return self._data

    @data.setter
    def data(self, value: np.ndarray) -> None:
        if value.shape != self.shape:
            raise ValueError(f"Expected shape {self.shape}, got {value.shape}")
        if value.dtype != self._dtype:
            value = value.astype(self._dtype)
        if not value.flags.writeable:
            value = value.copy()
        self._data = value

    def get(self, x: int, y: int) -> int:
        """Get cell state with toroidal wrapping."""
        y = y % self._height
        x = x % self._width
        return int(self._data[y, x])

    def set(self, x: int, y: int, value: int) -> None:
        """Set cell state with toroidal wrapping."""
        y = y % self._height
        x = x % self._width
        self._data[y, x] = value

    def reset(self) -> None:
        """Set all cells to state 0."""
        self._data.fill(0)

    def random_fill(
        self,
        rng: np.random.Generator,
        density: float = 0.5,
        states: list[int] | None = None,
    ) -> None:
        """Fill grid randomly.

        Args:
            rng: NumPy random generator.
            density: Fraction of cells to set non-zero.
            states: List of states to choose from (default: [1]).
        """
        self.reset()
        if states is None:
            states = [1]
        states = [s for s in states if s != 0]
        if not states:
            return

        mask = rng.random(self.shape) < density
        choices = rng.choice(states, size=self.shape)
        self._data[mask] = choices[mask]

    def copy(self) -> Grid:
        """Create a deep copy."""
        g = Grid(self._width, self._height, self._dtype)
        g._data = self._data.copy()
        return g

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Grid):
            return NotImplemented
        return (
            self._width == other._width
            and self._height == other._height
            and np.array_equal(self._data, other._data)
        )

    def __repr__(self) -> str:
        return f"Grid({self._width}x{self._height}, dtype={self._dtype})"
