"""Base plugin registry and metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")


@dataclass
class PluginMeta:
    """Metadata for a registered plugin."""

    name: str
    category: str = ""
    description: str = ""
    author: str = ""
    version: str = ""
    # Extra metadata specific to plugin type
    extra: dict[str, Any] = field(default_factory=dict)


class PluginRegistry(Generic[T]):
    """Generic plugin registry with decorator-based registration."""

    def __init__(self) -> None:
        self._plugins: dict[str, T] = {}
        self._meta: dict[str, PluginMeta] = {}

    def register(self, name: str, plugin: T, meta: PluginMeta | None = None) -> None:
        """Register a plugin by name."""
        self._plugins[name] = plugin
        self._meta[name] = meta or PluginMeta(name=name)

    def get(self, name: str) -> T:
        """Retrieve a plugin by name."""
        if name not in self._plugins:
            raise KeyError(f"Plugin '{name}' not found. Available: {list(self._plugins.keys())}")
        return self._plugins[name]

    def list(self, category: str | None = None) -> list[PluginMeta]:
        """List all registered plugins, optionally filtered by category."""
        meta_list = list(self._meta.values())
        if category:
            meta_list = [m for m in meta_list if m.category == category]
        return sorted(meta_list, key=lambda m: m.name)

    def names(self) -> list[str]:
        """List all registered plugin names."""
        return sorted(self._plugins.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._plugins

    def __repr__(self) -> str:
        return f"PluginRegistry({len(self._plugins)} plugins)"
