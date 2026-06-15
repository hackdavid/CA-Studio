"""Logger for metrics time series export."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


class MetricsLogger:
    """Collect and export metrics over time."""

    def __init__(self, output_dir: Path, format: str = "csv") -> None:
        self.output_dir = Path(output_dir)
        self.format = format
        self._data: list[dict[str, Any]] = []

    def on_step(self, step: int, metrics: dict[str, Any]) -> None:
        """Record metrics for one step."""
        row = {"step": step}
        row.update(metrics)
        self._data.append(row)

    def on_experiment_end(self) -> None:
        """Export collected metrics to file."""
        if not self._data:
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(self._data)

        if self.format == "csv":
            path = self.output_dir / "metrics.csv"
            df.to_csv(path, index=False)
        elif self.format == "parquet":
            path = self.output_dir / "metrics.parquet"
            df.to_parquet(path, index=False)
        elif self.format == "json":
            path = self.output_dir / "metrics.json"
            df.to_json(path, orient="records", indent=2)
        else:
            raise ValueError(f"Unknown format: {self.format}")

    def __repr__(self) -> str:
        return f"MetricsLogger({len(self._data)} steps, format={self.format})"
