"""Seed / initial state configurations for the board."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


class SeedType(str, Enum):
    """Type of initial seed pattern."""

    SINGLE = "single"
    RANDOM = "random"
    FILE = "file"
    PATTERN = "pattern"


class SeedConfig(BaseModel):
    """Configuration for board initial state."""

    type: SeedType
    state: int = 1
    position: str = "center"  # "center", "random", or "custom"
    custom_x: int | None = None
    custom_y: int | None = None
    density: float = 0.0  # For RANDOM: fraction of cells to fill
    states: list[int] | None = None  # For RANDOM: which states to use
    file_path: str | None = None  # For FILE
    pattern: list[list[int]] | None = None  # For PATTERN

    def apply(self, board: Any, rng: Any) -> None:
        """Apply this seed configuration to a board.

        Args:
            board: A Board instance.
            rng: A numpy.random.Generator.
        """
        from .board import Board

        if not isinstance(board, Board):
            raise TypeError("Expected Board instance")

        board.reset()

        if self.type == SeedType.SINGLE:
            if self.position == "center":
                board.set_centered(0, 0, self.state)
            elif self.position == "random":
                x = rng.integers(0, board.width)
                y = rng.integers(0, board.height)
                board.set(x, y, self.state)
            elif self.position == "custom" and self.custom_x is not None and self.custom_y is not None:
                board.set(self.custom_x, self.custom_y, self.state)
            else:
                board.set_centered(0, 0, self.state)

        elif self.type == SeedType.RANDOM:
            states = self.states if self.states else [self.state]
            board.random_fill(rng, density=self.density, states=states)

        elif self.type == SeedType.FILE:
            raise NotImplementedError("FILE seed not yet implemented")

        elif self.type == SeedType.PATTERN:
            if self.pattern:
                _apply_pattern(board, self.pattern)


def _apply_pattern(board: Any, pattern: list[list[int]]) -> None:
    """Apply a 2D pattern centered on the board."""
    ph = len(pattern)
    pw = len(pattern[0]) if ph > 0 else 0
    cy = board.center_y
    cx = board.center_x
    for dy, row in enumerate(pattern):
        for dx, state in enumerate(row):
            x = cx - pw // 2 + dx
            y = cy - ph // 2 + dy
            board.set(x, y, state)
