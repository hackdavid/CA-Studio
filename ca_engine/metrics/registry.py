"""Metric registry with built-in metrics."""

from __future__ import annotations

from typing import Any

from .base import Metric
from .density import DensityMetric
from .entropy import EntropyMetric
from ..plugins.base import PluginRegistry, PluginMeta


class MetricRegistry:
    """Registry for metric plugins."""

    def __init__(self) -> None:
        self._registry = PluginRegistry[Metric]()
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register all built-in metrics."""
        self.register("density", DensityMetric, "structure", "Fraction of non-zero cells")
        self.register("entropy", EntropyMetric, "structure", "Shannon entropy over all states")
        self.register("entropy_nonzero", lambda: EntropyMetric(exclude_zero=True), "structure", "Shannon entropy excluding state 0")

    def register(
        self,
        name: str,
        factory: Any,
        category: str = "",
        description: str = "",
    ) -> None:
        """Register a metric by name.

        Args:
            name: Metric name.
            factory: Callable that returns a Metric instance.
            category: Metric category.
            description: Human-readable description.
        """
        meta = PluginMeta(name=name, category=category, description=description)
        self._registry.register(name, factory, meta)

    def get(self, name: str | dict[str, Any]) -> Metric:
        """Get a metric instance by name.

        Args:
            name: Metric name string, or dict with 'name' key and optional config.

        Returns:
            Metric instance.
        """
        if isinstance(name, dict):
            metric_name = name.get("name", "")
            config = name
        else:
            metric_name = name
            config = {}

        if metric_name not in self._registry:
            raise KeyError(f"Metric '{metric_name}' not found. Available: {self._registry.names()}")

        factory = self._registry.get(metric_name)
        if callable(factory):
            metric = factory()
        else:
            metric = factory

        return metric

    def list(self, category: str | None = None) -> list[PluginMeta]:
        return self._registry.list(category)

    def names(self) -> list[str]:
        return self._registry.names()

    def __contains__(self, name: str) -> bool:
        return name in self._registry

    def __repr__(self) -> str:
        return f"MetricRegistry({len(self._registry.names())} metrics)"
