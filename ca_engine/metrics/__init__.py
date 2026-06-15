"""Metrics plugin system for CA Lab."""

from .base import Metric
from .density import DensityMetric
from .entropy import EntropyMetric
from .registry import MetricRegistry

__all__ = [
    "Metric",
    "DensityMetric",
    "EntropyMetric",
    "MetricRegistry",
]
