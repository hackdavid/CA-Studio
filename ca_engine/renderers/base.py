"""Base renderer class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class Renderer(ABC):
    """Abstract base class for renderers.

    Renderers receive the raw uint8 grid state and palette, and produce
    visual output appropriate for their target environment.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Renderer name."""
        ...

    @property
    def is_live(self) -> bool:
        """Whether this renderer has its own event loop."""
        return False

    @abstractmethod
    def render(self, grid: np.ndarray, metrics: dict[str, Any] | None = None) -> Any:
        """Render one frame.

        Args:
            grid: State grid of shape (H, W), dtype uint8.
            metrics: Optional metrics dict to display.

        Returns:
            Displayable object or action string.
        """
        ...

    def close(self) -> None:
        """Clean up resources."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
