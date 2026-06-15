"""StepResult dataclass for simulation output."""

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class StepResult:
    """Result of a single simulation step.

    Attributes:
        grid: Board state after the step, shape (H, W), uint8.
        metrics: Dictionary of metric name → value.
        step: Step number.
    """

    grid: np.ndarray
    metrics: dict[str, Any]
    step: int
