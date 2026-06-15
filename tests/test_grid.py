"""Tests for Grid and Board."""

import numpy as np
import pytest

from ca_engine.core.grid import Grid
from ca_engine.core.board import Board
from ca_engine.core.palette import Palette


class TestGrid:
    def test_init(self):
        g = Grid(10, 10)
        assert g.width == 10
        assert g.height == 10
        assert g.shape == (10, 10)
        assert g.data.dtype == np.uint8
        assert np.all(g.data == 0)

    def test_set_get(self):
        g = Grid(5, 5)
        g.set(2, 2, 1)
        assert g.get(2, 2) == 1

    def test_toroidal_wrap(self):
        g = Grid(5, 5)
        g.set(5, 5, 3)  # Should wrap to (0,0)
        assert g.get(0, 0) == 3
        g.set(-1, -1, 7)  # Should wrap to (4,4)
        assert g.get(4, 4) == 7

    def test_reset(self):
        g = Grid(5, 5)
        g.set(1, 1, 1)
        g.reset()
        assert np.all(g.data == 0)

    def test_random_fill(self):
        rng = np.random.default_rng(42)
        g = Grid(10, 10)
        g.random_fill(rng, density=0.5, states=[1, 2])
        non_zero = np.count_nonzero(g.data)
        assert 30 < non_zero < 70  # Probabilistic, but with seed 42 should be consistent

    def test_copy(self):
        g = Grid(5, 5)
        g.set(1, 1, 1)
        c = g.copy()
        assert c == g
        c.set(1, 1, 2)
        assert c != g

    def test_equality(self):
        g1 = Grid(5, 5)
        g2 = Grid(5, 5)
        assert g1 == g2
        g2.set(0, 0, 1)
        assert g1 != g2


class TestBoard:
    def test_init(self):
        b = Board(32, 32)
        assert b.width == 32
        assert b.height == 32
        assert b.center_x == 16
        assert b.center_y == 16

    def test_set_updates_bbox(self):
        b = Board(32, 32)
        # Set cell to the right/below of center (center is 16,16)
        b.set(20, 20, 1)
        assert b.min_x == 16
        assert b.max_x == 20
        assert b.min_y == 16
        assert b.max_y == 20
        # Now set a cell to the left/above
        b.set(10, 10, 1)
        assert b.min_x == 10
        assert b.max_x == 20
        assert b.min_y == 10
        assert b.max_y == 20

    def test_set_centered(self):
        b = Board(32, 32)
        b.set_centered(0, 0, 1)
        assert b.get(b.center_x, b.center_y) == 1

    def test_resize(self):
        b = Board(32, 32)
        b.set(10, 10, 1)
        b.resize(64, 64)
        assert b.width == 64
        assert b.height == 64
        assert b.center_x == 32
        assert b.center_y == 32
        # The old (10,10) should be near (32-16+10, 32-16+10) = (26, 26)
        assert b.get(26, 26) == 1

    def test_reset(self):
        b = Board(32, 32)
        b.set(10, 10, 1)
        b.reset()
        assert np.all(b.data == 0)
        assert b.min_x == b.center_x

    def test_to_rgb(self):
        b = Board(4, 4)
        palette = Palette.default(num_colors=4)
        b.set(0, 0, 1)
        b.set(1, 1, 2)
        rgb = b.to_rgb(palette)
        assert rgb.shape == (4, 4, 3)
        assert np.array_equal(rgb[0, 0], palette.colors[1])
        assert np.array_equal(rgb[1, 1], palette.colors[2])

    def test_copy_from(self):
        b1 = Board(32, 32)
        b1.set(10, 10, 1)
        b2 = Board(32, 32)
        b2.copy_from(b1)
        assert np.array_equal(b1.data, b2.data)
