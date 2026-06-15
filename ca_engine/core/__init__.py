"""Core simulation engine — grid, board, neighbourhoods, simulator."""

from .grid import Grid
from .board import Board
from .neighbourhood import Neighbourhood, N4, N5, N8, N9
from .palette import Palette
from .seed import SeedType, SeedConfig
from .simulator import Simulator, StepResult

__all__ = [
    "Grid",
    "Board",
    "Neighbourhood",
    "N4",
    "N5",
    "N8",
    "N9",
    "Palette",
    "SeedType",
    "SeedConfig",
    "Simulator",
    "StepResult",
]
