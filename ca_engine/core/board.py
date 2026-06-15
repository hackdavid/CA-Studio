"""Board with bounding-box tracking, resize, and centered coordinates."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from .grid import Grid

if TYPE_CHECKING:
    from .palette import Palette


class Board(Grid):
    """A Grid with bounding-box tracking and centered coordinates.

    Tracks minX/maxX/minY/maxY to quickly find the region containing live cells.
    """

    def __init__(self, width: int, height: int, dtype: np.dtype = np.uint8) -> None:
        super().__init__(width, height, dtype)
        self._center_x = width // 2
        self._center_y = height // 2
        self._min_x = self._center_x
        self._max_x = self._center_x
        self._min_y = self._center_y
        self._max_y = self._center_y

    @property
    def center_x(self) -> int:
        return self._center_x

    @property
    def center_y(self) -> int:
        return self._center_y

    @property
    def min_x(self) -> int:
        return self._min_x

    @property
    def max_x(self) -> int:
        return self._max_x

    @property
    def min_y(self) -> int:
        return self._min_y

    @property
    def max_y(self) -> int:
        return self._max_y

    def set(self, x: int, y: int, value: int) -> None:
        """Set cell with toroidal wrap and bounding-box update."""
        y = y % self._height
        x = x % self._width
        if value != 0:
            self._update_min_max(x, y)
        self._data[y, x] = value

    def set_centered(self, x: int, y: int, value: int) -> None:
        """Set cell using coordinates with origin at board center."""
        self.set(x + self._center_x, y + self._center_y, value)

    def get_centered(self, x: int, y: int) -> int:
        """Get cell using coordinates with origin at board center."""
        return self.get(x + self._center_x, y + self._center_y)

    def _update_min_max(self, x: int, y: int) -> None:
        if x < self._min_x:
            self._min_x = x
        if x > self._max_x:
            self._max_x = x
        if y < self._min_y:
            self._min_y = y
        if y > self._max_y:
            self._max_y = y

    def tighten_min_max(self) -> None:
        """Recompute min/max by scanning the grid."""
        live = self._data > 0
        if not live.any():
            self._min_x = self._center_x
            self._max_x = self._center_x
            self._min_y = self._center_y
            self._max_y = self._center_y
            return

        rows, cols = np.where(live)
        self._min_x = int(cols.min())
        self._max_x = int(cols.max())
        self._min_y = int(rows.min())
        self._max_y = int(rows.max())

    def reset(self) -> None:
        """Clear grid and reset bounding box."""
        super().reset()
        self._min_x = self._center_x
        self._max_x = self._center_x
        self._min_y = self._center_y
        self._max_y = self._center_y

    def resize(self, new_width: int, new_height: int) -> None:
        """Resize board, preserving cells near the center."""
        new_center_x = new_width // 2
        new_center_y = new_height // 2
        x_change = new_center_x - self._center_x
        y_change = new_center_y - self._center_y

        new_data = np.zeros((new_height, new_width), dtype=self._dtype)

        # Copy overlapping region
        old_h, old_w = self._data.shape
        src_y_start = max(0, -y_change)
        src_y_end = min(old_h, new_height - y_change)
        src_x_start = max(0, -x_change)
        src_x_end = min(old_w, new_width - x_change)

        dst_y_start = max(0, y_change)
        dst_x_start = max(0, x_change)

        copy_h = src_y_end - src_y_start
        copy_w = src_x_end - src_x_start

        if copy_h > 0 and copy_w > 0:
            new_data[
                dst_y_start : dst_y_start + copy_h,
                dst_x_start : dst_x_start + copy_w,
            ] = self._data[src_y_start:src_y_end, src_x_start:src_x_end]

        self._width = new_width
        self._height = new_height
        self._data = new_data
        self._center_x = new_center_x
        self._center_y = new_center_y
        self.tighten_min_max()

    def copy_from(self, other: Board) -> None:
        """Copy state from another board, resizing if needed."""
        if other._width != self._width or other._height != self._height:
            temp = other.copy()
            temp.resize(self._width, self._height)
            other = temp
        self._data = other._data.copy()
        self._min_x = other._min_x
        self._max_x = other._max_x
        self._min_y = other._min_y
        self._max_y = other._max_y

    def copy(self) -> Board:
        """Deep copy."""
        b = Board(self._width, self._height, self._dtype)
        b._data = self._data.copy()
        b._min_x = self._min_x
        b._max_x = self._max_x
        b._min_y = self._min_y
        b._max_y = self._max_y
        return b

    def random_fill(
        self,
        rng: np.random.Generator,
        density: float = 0.5,
        states: list[int] | None = None,
    ) -> None:
        """Fill grid randomly, then tighten bounds."""
        super().random_fill(rng, density, states)
        self.tighten_min_max()

    def to_rgb(self, palette: Palette) -> np.ndarray:
        """Convert state grid to RGB image using palette.

        Returns array of shape (H, W, 3) with uint8 RGB values.
        """
        return palette.colors[self._data]

    def __repr__(self) -> str:
        return f"Board({self._width}x{self._height}, bbox=({self._min_x},{self._min_y})-({self._max_x},{self._max_y}))"
