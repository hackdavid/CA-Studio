"""Tests for metrics plugin system."""

import numpy as np
import pytest

from ca_engine.metrics.base import Metric
from ca_engine.metrics.density import DensityMetric
from ca_engine.metrics.entropy import EntropyMetric
from ca_engine.metrics.registry import MetricRegistry


class TestDensityMetric:
    def test_init(self):
        m = DensityMetric()
        assert m.name == "density"
        m.on_init((32, 32), 2)
        assert m.value == 0.0

    def test_on_step(self):
        m = DensityMetric()
        m.on_init((4, 4), 2)
        grid = np.array([
            [0, 1, 0, 1],
            [1, 0, 0, 0],
            [0, 0, 1, 1],
            [0, 0, 0, 0],
        ], dtype=np.uint8)
        m.on_step(grid, 1)
        assert m.value == 5 / 16

    def test_on_cell_update(self):
        m = DensityMetric()
        m.on_init((4, 4), 2)
        m.on_cell_update(0, 1, 0, 0)
        assert m.value == 1 / 16
        m.on_cell_update(1, 0, 0, 0)
        assert m.value == 0.0

    def test_values(self):
        m = DensityMetric()
        m.on_init((4, 4), 2)
        vals = m.values
        assert "density" in vals
        assert vals["density"] == 0.0


class TestEntropyMetric:
    def test_init(self):
        m = EntropyMetric()
        assert m.name == "entropy"
        m.on_init((32, 32), 2)
        assert m.value == 0.0

    def test_uniform(self):
        """Uniform distribution has max entropy = log2(K)."""
        m = EntropyMetric()
        m.on_init((4, 4), 2)
        grid = np.array([
            [0, 1, 0, 1],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [1, 0, 1, 0],
        ], dtype=np.uint8)
        m.on_step(grid, 1)
        # 50/50 distribution, entropy = 1.0
        assert abs(m.value - 1.0) < 0.01

    def test_all_same(self):
        """All same state has zero entropy."""
        m = EntropyMetric()
        m.on_init((4, 4), 2)
        grid = np.ones((4, 4), dtype=np.uint8)
        m.on_step(grid, 1)
        assert m.value == 0.0

    def test_exclude_zero(self):
        m = EntropyMetric(exclude_zero=True)
        assert m.name == "entropy_nonzero"
        m.on_init((4, 4), 3)
        grid = np.array([
            [0, 1, 0, 2],
            [1, 0, 2, 0],
            [0, 1, 0, 2],
            [1, 0, 2, 0],
        ], dtype=np.uint8)
        m.on_step(grid, 1)
        # States 1 and 2 each have 4 cells, 50/50
        assert abs(m.value - 1.0) < 0.01


class TestMetricRegistry:
    def test_builtins(self):
        r = MetricRegistry()
        assert "density" in r
        assert "entropy" in r
        assert "entropy_nonzero" in r

    def test_get(self):
        r = MetricRegistry()
        m = r.get("density")
        assert isinstance(m, DensityMetric)
        assert m.name == "density"

    def test_list(self):
        r = MetricRegistry()
        names = r.names()
        assert "density" in names
        assert "entropy" in names

    def test_unknown(self):
        r = MetricRegistry()
        with pytest.raises(KeyError):
            r.get("nonexistent")
