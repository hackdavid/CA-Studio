"""Decorators for registering plugins."""

from __future__ import annotations

from typing import Any, Callable

from .base import PluginMeta, PluginRegistry

# Global registries
_rule_registry: PluginRegistry[Any] = PluginRegistry()
_metric_registry: PluginRegistry[Any] = PluginRegistry()
_renderer_registry: PluginRegistry[Any] = PluginRegistry()
_logger_registry: PluginRegistry[Any] = PluginRegistry()
_state_preset_registry: PluginRegistry[Any] = PluginRegistry()


def rule(name: str, category: str = "", description: str = "", **extra: Any) -> Callable[[T], T]:
    """Decorator to register a rule plugin."""
    def decorator(cls: T) -> T:
        meta = PluginMeta(name=name, category=category, description=description, extra=extra)
        _rule_registry.register(name, cls, meta)
        return cls
    return decorator


def metric(name: str, category: str = "", description: str = "", **extra: Any) -> Callable[[T], T]:
    """Decorator to register a metric plugin."""
    def decorator(cls: T) -> T:
        meta = PluginMeta(name=name, category=category, description=description, extra=extra)
        _metric_registry.register(name, cls, meta)
        return cls
    return decorator


def renderer(name: str, category: str = "", description: str = "", **extra: Any) -> Callable[[T], T]:
    """Decorator to register a renderer plugin."""
    def decorator(cls: T) -> T:
        meta = PluginMeta(name=name, category=category, description=description, extra=extra)
        _renderer_registry.register(name, cls, meta)
        return cls
    return decorator


def logger(name: str, category: str = "", description: str = "", **extra: Any) -> Callable[[T], T]:
    """Decorator to register a logger plugin."""
    def decorator(cls: T) -> T:
        meta = PluginMeta(name=name, category=category, description=description, extra=extra)
        _logger_registry.register(name, cls, meta)
        return cls
    return decorator


def state_preset(name: str, category: str = "", description: str = "", **extra: Any) -> Callable[[T], T]:
    """Decorator to register a state preset."""
    def decorator(cls: T) -> T:
        meta = PluginMeta(name=name, category=category, description=description, extra=extra)
        _state_preset_registry.register(name, cls, meta)
        return cls
    return decorator


# Export registry getters for application code
def get_rule_registry() -> PluginRegistry[Any]:
    return _rule_registry


def get_metric_registry() -> PluginRegistry[Any]:
    return _metric_registry


def get_renderer_registry() -> PluginRegistry[Any]:
    return _renderer_registry


def get_logger_registry() -> PluginRegistry[Any]:
    return _logger_registry


def get_state_preset_registry() -> PluginRegistry[Any]:
    return _state_preset_registry
