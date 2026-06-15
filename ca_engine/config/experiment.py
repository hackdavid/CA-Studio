"""Pydantic models for experiment configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SeedConfig(BaseModel):
    """Configuration for initial board state."""

    type: str = "single"  # "single", "random", "file", "pattern"
    state: int = 1
    position: str = "center"  # "center", "random", "custom"
    custom_x: int | None = None
    custom_y: int | None = None
    density: float = Field(default=0.0, ge=0.0, le=1.0)
    states: list[int] | None = None
    file_path: str | None = None
    pattern: list[list[int]] | None = None


class LogConfig(BaseModel):
    """Configuration for experiment logging."""

    enabled: bool = True
    output_dir: Path = Path("runs")
    format: str = "csv"  # "csv", "parquet", "json"
    metrics_every: int = Field(default=1, ge=1)
    frames_every: int | None = None
    animation: bool = False
    provenance: bool = True


class ExperimentConfig(BaseModel):
    """Full experiment configuration."""

    name: str = "experiment"
    state_preset: str | None = None  # "conway", "413", etc.
    rule: str = "Conway"
    neighbourhood: str = "moore8"
    board: list[int] = Field(default=[32, 32])
    num_states: int = Field(default=2, ge=2, le=256)
    seed: SeedConfig = Field(default_factory=SeedConfig)
    steps: int = Field(default=100, ge=1)
    global_seed: int | None = None
    metrics: list[str | dict[str, Any]] = Field(default_factory=list)
    log: LogConfig = Field(default_factory=LogConfig)
    palette: str | None = None  # Path to ColourSetup.txt, or None for default
    renderer: str | None = None
    cell_size: int = Field(default=4, ge=1)
    show_grid: bool = True  # Show grid lines between cells

    @field_validator("board")
    @classmethod
    def validate_board(cls, v: list[int]) -> list[int]:
        if len(v) != 2:
            raise ValueError("Board must be [width, height]")
        if v[0] < 1 or v[1] < 1:
            raise ValueError("Board dimensions must be positive")
        return v

    @field_validator("neighbourhood")
    @classmethod
    def validate_neighbourhood(cls, v: str) -> str:
        valid = {"n4", "n5", "n8", "n9", "von_neumann", "moore", "moore8", "moore9"}
        if v.lower() not in valid:
            raise ValueError(f"Unknown neighbourhood: {v}")
        return v

    @property
    def width(self) -> int:
        return self.board[0]

    @property
    def height(self) -> int:
        return self.board[1]
