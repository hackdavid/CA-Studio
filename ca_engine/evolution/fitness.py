"""Fitness evaluation for evolved CA candidates."""

from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim

from ca_engine.core.simulator import Simulator
from ca_engine.metrics.registry import MetricRegistry


class FitnessEvaluator:
    """Evaluate how close a simulation result is to a target."""

    def __init__(
        self,
        target_grid: np.ndarray | None = None,
        target_metrics: dict[str, float] | None = None,
        weights: dict[str, float] | None = None,
        steps: int = 20,
        width: int = 32,
        height: int = 32,
    ) -> None:
        """
        Args:
            target_grid: Target grid state to compare against (H×W uint8).
            target_metrics: Target CA metrics values (density, entropy, etc.).
            weights: Dict with keys 'similarity', 'metrics', 'simplicity'.
            steps: Number of simulation steps to run before evaluation.
            width: Board width.
            height: Board height.
        """
        self.target_grid = target_grid
        self.target_metrics = target_metrics or {}
        self.weights = weights or {"similarity": 0.5, "metrics": 0.3, "simplicity": 0.2}
        self.steps = steps
        self.width = width
        self.height = height

        self._metric_registry = MetricRegistry()
        self._metric_names = list(self.target_metrics.keys()) if self.target_metrics else ["density", "entropy"]

    def evaluate(self, chromosome) -> float:
        """Run simulation and return composite fitness score [0, 1]."""
        sim = chromosome.to_simulator(self.width, self.height)

        # Attach metrics
        for name in self._metric_names:
            try:
                metric = self._metric_registry.get(name)
                metric.on_init((self.height, self.width), chromosome.num_states)
                sim.attach_metric(metric)
            except KeyError:
                pass

        # Run
        for _ in range(self.steps):
            sim.step()

        final_grid = sim.board.data
        metrics = sim._collect_metrics()

        scores = {}

        # 1. Grid similarity (SSIM or MSE-based)
        if self.target_grid is not None:
            scores["similarity"] = self._grid_similarity(final_grid, self.target_grid)
        else:
            scores["similarity"] = 0.5  # neutral if no target

        # 2. Metrics match
        if self.target_metrics:
            scores["metrics"] = self._metrics_match(metrics, self.target_metrics)
        else:
            scores["metrics"] = 0.5

        # 3. Simplicity (fewer distinct transitions = higher score)
        scores["simplicity"] = self._simplicity_score(chromosome)

        # Weighted composite
        total = 0.0
        total_weight = 0.0
        for key, weight in self.weights.items():
            total += scores.get(key, 0.5) * weight
            total_weight += weight

        return total / total_weight if total_weight > 0 else 0.5

    @staticmethod
    def _grid_similarity(grid: np.ndarray, target: np.ndarray) -> float:
        """Compute SSIM-based similarity between two grids."""
        try:
            # SSIM expects float64 and range [0, 1] or [0, 255]
            # Normalize to [0, 1]
            g = grid.astype(np.float64) / max(grid.max(), 1)
            t = target.astype(np.float64) / max(target.max(), 1)
            # SSIM for 2D arrays
            score = ssim(g, t, data_range=1.0)
            # score is in [-1, 1]; normalize to [0, 1]
            return float((score + 1) / 2)
        except Exception:
            # Fallback to inverse MSE
            mse = float(np.mean((grid.astype(np.float32) - target.astype(np.float32)) ** 2))
            max_mse = 255.0 ** 2
            return max(0.0, 1.0 - mse / max_mse)

    @staticmethod
    def _metrics_match(actual: dict[str, Any], target: dict[str, float]) -> float:
        """Compare actual metrics to target metrics."""
        if not target:
            return 0.5
        similarities = []
        for key, target_val in target.items():
            actual_val = actual.get(key)
            if actual_val is None or not isinstance(actual_val, (int, float)):
                continue
            # Normalize by max value
            denom = max(abs(target_val), abs(actual_val), 1.0)
            sim = 1.0 - abs(target_val - actual_val) / denom
            similarities.append(max(0.0, sim))
        return float(np.mean(similarities)) if similarities else 0.5

    @staticmethod
    def _simplicity_score(chromosome) -> float:
        """Reward simple rule tables."""
        table = chromosome.rule_table
        total_cells = table.size
        unique_transitions = len(np.unique(table))
        # Fewer unique transitions = simpler
        # Normalize: if only 1 unique transition, score = 1.0
        # If all cells are different, score = 0.0
        return max(0.0, 1.0 - (unique_transitions - 1) / max(total_cells - 1, 1))
