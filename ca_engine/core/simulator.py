"""Simulator: orchestrates grid, rule, neighbourhood, and metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .board import Board
from .neighbourhood import Neighbourhood
from .palette import Palette
from .seed import SeedConfig
from ..rules.compiler import RuleTable


@dataclass
class StepResult:
    """Result of a single simulation step."""

    grid: np.ndarray
    metrics: dict[str, Any]
    step: int


class Simulator:
    """Main simulation engine.

    Holds the board, rule table, neighbourhood, and palette.
    Steps forward by applying the rule synchronously.
    """

    def __init__(
        self,
        board: Board,
        rule_table: RuleTable,
        neighbourhood: Neighbourhood,
        palette: Palette | None = None,
        rng: np.random.Generator | None = None,
    ) -> None:
        self.board = board
        self.rule_table = rule_table
        self.neighbourhood = neighbourhood
        self.palette = palette or Palette.default()
        self.rng = rng or np.random.default_rng()
        self.step_num = 0
        self._metrics: list[Any] = []

    @classmethod
    def from_config(
        cls,
        width: int = 32,
        height: int = 32,
        rule_table: RuleTable | None = None,
        neighbourhood: Neighbourhood | str = Neighbourhood.N8,
        palette: Palette | None = None,
        seed: int | None = None,
    ) -> Simulator:
        """Create a simulator from basic parameters."""
        board = Board(width, height)
        if isinstance(neighbourhood, str):
            neighbourhood = Neighbourhood.from_name(neighbourhood)
        rng = np.random.default_rng(seed)
        sim = cls(board, rule_table or RuleTable(np.zeros((2, 10), dtype=np.uint8)), neighbourhood, palette, rng)
        return sim

    def reset(self, seed_config: SeedConfig | None = None) -> None:
        """Reset board to initial state."""
        if seed_config is None:
            seed_config = SeedConfig(type="single", state=1)
        seed_config.apply(self.board, self.rng)
        self.step_num = 0

    def step(self, n: int = 1) -> StepResult:
        """Advance simulation by n steps.

        Uses double-buffering: reads from current board, writes to new grid,
        then swaps. This prevents read-after-write corruption in the same step.
        """
        for _ in range(n):
            counts = self.neighbourhood.count(self.board)
            next_grid = self.rule_table.lookup(self.board.data, counts)
            self.board.data = next_grid
            self.board.tighten_min_max()
            self.step_num += 1

        return StepResult(
            grid=self.board.data.copy(),
            metrics=self._collect_metrics(),
            step=self.step_num,
        )

    def run(self, steps: int) -> list[StepResult]:
        """Run for a number of steps and return results."""
        return [self.step() for _ in range(steps)]

    def attach_metric(self, metric: Any) -> None:
        """Attach a metric plugin."""
        self._metrics.append(metric)

    def _collect_metrics(self) -> dict[str, Any]:
        """Collect metrics from all attached plugins."""
        result = {}
        for metric in self._metrics:
            if hasattr(metric, "on_step"):
                metric.on_step(self.board.data, self.step_num)
            if hasattr(metric, "values"):
                vals = metric.values
                # Flatten only when values has a single key matching metric name
                if len(vals) == 1 and metric.name in vals:
                    result[metric.name] = vals[metric.name]
                else:
                    result[metric.name] = vals
            elif hasattr(metric, "name") and hasattr(metric, "value"):
                result[metric.name] = metric.value
        return result

    @property
    def grid_shape(self) -> tuple[int, int]:
        return (self.board.height, self.board.width)

    def __repr__(self) -> str:
        return f"Simulator({self.board.width}x{self.board.height}, step={self.step_num}, rule={self.rule_table.name!r})"
