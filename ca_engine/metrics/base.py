"""Base class for all metrics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class Metric(ABC):
    """Abstract base class for metrics that measure board state.

    Metrics can update incrementally on cell changes or recompute on step.
    """

    def __init__(self) -> None:
        self._enabled = True

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable metric name."""
        ...

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def on_init(self, grid_shape: tuple[int, int], num_states: int) -> None:
        """Called when the metric is attached to a simulator."""
        pass

    def on_step(self, grid: np.ndarray, step_num: int) -> None:
        """Called after each simulation step."""
        pass

    def on_cell_update(self, old: int, new: int, x: int, y: int) -> None:
        """Called when a single cell is modified by user interaction."""
        pass

    def reset(self) -> None:
        """Reset metric state."""
        pass

    @property
    @abstractmethod
    def values(self) -> dict[str, Any]:
        """Return current metric values as a dict."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
