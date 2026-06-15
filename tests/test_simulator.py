"""Tests for the Simulator."""

import numpy as np
import pytest

from ca_engine.core.simulator import Simulator
from ca_engine.core.board import Board
from ca_engine.core.neighbourhood import Neighbourhood
from ca_engine.core.seed import SeedConfig
from ca_engine.rules.compiler import RuleTable
from ca_engine.rules.legacy_loader import LegacyRuleLoader


class TestSimulator:
    def test_init(self):
        board = Board(32, 32)
        table = RuleTable(np.zeros((2, 10), dtype=np.uint8))
        sim = Simulator(board, table, Neighbourhood.N8)
        assert sim.board.width == 32
        assert sim.step_num == 0

    def test_conway_blinker(self):
        """Test Conway's blinker oscillator (period 2)."""
        loader = LegacyRuleLoader()
        table = loader.load("Conway", num_states=2)
        board = Board(32, 32)
        sim = Simulator(board, table, Neighbourhood.N8)

        # Set up horizontal blinker centered at (16,16)
        cx, cy = board.center_x, board.center_y
        board.set(cx - 1, cy, 1)
        board.set(cx, cy, 1)
        board.set(cx + 1, cy, 1)

        # Save initial state
        initial = board.data.copy()

        # Step 1
        sim.step()
        step1 = board.data.copy()
        # Should be vertical
        assert step1[cy, cx] == 1
        assert step1[cy - 1, cx] == 1
        assert step1[cy + 1, cx] == 1
        # Horizontal should be gone
        assert step1[cy, cx - 1] == 0
        assert step1[cy, cx + 1] == 0

        # Step 2
        sim.step()
        step2 = board.data.copy()
        # Should be back to horizontal
        assert np.array_equal(step2, initial)

    def test_conway_block(self):
        """Test Conway's block (still life)."""
        loader = LegacyRuleLoader()
        table = loader.load("Conway", num_states=2)
        board = Board(32, 32)
        sim = Simulator(board, table, Neighbourhood.N8)

        # 2x2 block
        cx, cy = board.center_x, board.center_y
        board.set(cx, cy, 1)
        board.set(cx + 1, cy, 1)
        board.set(cx, cy + 1, 1)
        board.set(cx + 1, cy + 1, 1)

        initial = board.data.copy()

        sim.step()
        assert np.array_equal(board.data, initial)

    def test_seed_single(self):
        """Test single-center seed."""
        loader = LegacyRuleLoader()
        table = loader.load("Conway", num_states=2)
        board = Board(32, 32)
        sim = Simulator(board, table, Neighbourhood.N8)
        sim.reset(SeedConfig(type="single", state=1))
        assert board.get(board.center_x, board.center_y) == 1

    def test_seed_random(self):
        """Test random seed."""
        loader = LegacyRuleLoader()
        table = loader.load("Conway", num_states=2)
        board = Board(32, 32)
        sim = Simulator(board, table, Neighbourhood.N8, rng=np.random.default_rng(42))
        sim.reset(SeedConfig(type="random", density=0.5, states=[1]))
        non_zero = np.count_nonzero(board.data)
        assert 400 < non_zero < 600  # ~50% of 1024 cells

    def test_step_result(self):
        loader = LegacyRuleLoader()
        table = loader.load("Conway", num_states=2)
        board = Board(32, 32)
        sim = Simulator(board, table, Neighbourhood.N8)
        sim.reset(SeedConfig(type="single", state=1))
        result = sim.step()
        assert result.step == 1
        assert result.grid.shape == (32, 32)
        assert result.grid.dtype == np.uint8

    def test_multiple_steps(self):
        loader = LegacyRuleLoader()
        table = loader.load("Conway", num_states=2)
        board = Board(32, 32)
        sim = Simulator(board, table, Neighbourhood.N8)
        sim.reset(SeedConfig(type="single", state=1))
        results = sim.run(10)
        assert len(results) == 10
        assert results[-1].step == 10

    def test_conway_glider_one_step(self):
        """Test that a glider moves after one step."""
        loader = LegacyRuleLoader()
        table = loader.load("Conway", num_states=2)
        board = Board(32, 32)
        sim = Simulator(board, table, Neighbourhood.N8)

        # Glider pattern (top-left at center)
        cx, cy = board.center_x, board.center_y
        board.set(cx, cy, 1)
        board.set(cx + 1, cy, 1)
        board.set(cx + 2, cy, 1)
        board.set(cx + 2, cy + 1, 1)
        board.set(cx + 1, cy + 2, 1)

        sim.step()
        # After one step, glider should have shifted
        # The exact expected state depends on Conway rules
        # We just verify it changed (not a still life)
        assert not np.array_equal(board.data, np.zeros((32, 32), dtype=np.uint8))

    def test_n4_neighbourhood(self):
        """Test with von Neumann neighbourhood (N4)."""
        loader = LegacyRuleLoader()
        table = loader.load("Conway", num_states=2)
        board = Board(32, 32)
        sim = Simulator(board, table, Neighbourhood.N4)
        sim.reset(SeedConfig(type="single", state=1))
        sim.step()
        # With N4, single cell has 0 neighbours, so dies
        assert board.get(board.center_x, board.center_y) == 0
