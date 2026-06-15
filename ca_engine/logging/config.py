"""Logging configuration models."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class LogConfig(BaseModel):
    """Configuration for experiment logging."""

    enabled: bool = True
    output_dir: Path = Path("runs")
    format: str = "csv"  # "csv", "parquet", "json"
    metrics_every: int = Field(default=1, ge=1)
    frames_every: int | None = None
    animation: bool = False
    provenance: bool = True
