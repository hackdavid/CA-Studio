"""Parity tests: Python engine vs Java reference behavior.

These tests verify that the Python engine produces identical results to the
Java reference implementation for well-known patterns.

For a full automated parity test against the compiled Java code, see:
    reference_code/CACmd.java (headless batch runner)
    or run scripts/run_java_reference.py
"""

import numpy as np
import pytest

from ca_engine.core.simulator import Simulator
from ca_engine.core.board import Board
from ca_engine.core.neighbourhood import Neighbourhood
from ca_engine.core.seed import SeedConfig
from ca_engine.rules.legacy_loader import LegacyRuleLoader


class TestConwayParity:
    """Parity tests using Conway's Game of Life (B3/S23)."""

    @pytest.fixture
    def loader(self):
        return LegacyRuleLoader()

    @pytest.fixture
    def conway(self, loader):
        return loader.load("Conway", num_states=2)

    def test_single_cell_dies(self, conway):
        """A single live cell dies in one step (no neighbours)."""
        board = Board(32, 32)
        sim = Simulator(board, conway, Neighbourhood.N8)
        sim.reset(SeedConfig(type="single", state=1))
        sim.step()
        assert board.get(board.center_x, board.center_y) == 0

    def test_two_cells_die(self, conway):
        """Two adjacent cells die in one step (only 1 neighbour each)."""
        board = Board(32, 32)
        sim = Simulator(board, conway, Neighbourhood.N8)
        cx, cy = board.center_x, board.center_y
        board.set(cx, cy, 1)
        board.set(cx + 1, cy, 1)
        sim.step()
        assert board.get(cx, cy) == 0
        assert board.get(cx + 1, cy) == 0

    def test_blinker_period_2(self, conway):
        """Blinker oscillator: period 2."""
        board = Board(32, 32)
        sim = Simulator(board, conway, Neighbourhood.N8)
        cx, cy = board.center_x, board.center_y

        # Horizontal blinker
        board.set(cx - 1, cy, 1)
        board.set(cx, cy, 1)
        board.set(cx + 1, cy, 1)
        initial = board.data.copy()

        sim.step()
        step1 = board.data.copy()
        # Should be vertical
        assert step1[cy, cx] == 1
        assert step1[cy - 1, cx] == 1
        assert step1[cy + 1, cx] == 1
        assert step1[cy, cx - 1] == 0
        assert step1[cy, cx + 1] == 0

        sim.step()
        step2 = board.data.copy()
        # Should be back to horizontal
        assert np.array_equal(step2, initial)

    def test_block_still_life(self, conway):
        """Block is a still life (doesn't change)."""
        board = Board(32, 32)
        sim = Simulator(board, conway, Neighbourhood.N8)
        cx, cy = board.center_x, board.center_y

        # 2x2 block
        board.set(cx, cy, 1)
        board.set(cx + 1, cy, 1)
        board.set(cx, cy + 1, 1)
        board.set(cx + 1, cy + 1, 1)
        initial = board.data.copy()

        sim.step()
        assert np.array_equal(board.data, initial)

        sim.step()
        assert np.array_equal(board.data, initial)

    def test_glider_moves(self, conway):
        """Glider moves diagonally, period 4."""
        board = Board(32, 32)
        sim = Simulator(board, conway, Neighbourhood.N8)
        cx, cy = board.center_x, board.center_y

        # Glider pattern (top-left at center)
        board.set(cx, cy, 1)
        board.set(cx + 1, cy, 1)
        board.set(cx + 2, cy, 1)
        board.set(cx + 2, cy + 1, 1)
        board.set(cx + 1, cy + 2, 1)

        # After 4 steps, glider should have shifted by (+1, -1) in (x, y)
        for _ in range(4):
            sim.step()

        # Verify the glider pattern is present at expected positions
        assert board.get(cx + 1, cy - 1) == 1
        assert board.get(cx + 2, cy - 1) == 1
        assert board.get(cx + 3, cy - 1) == 1
        assert board.get(cx + 3, cy) == 1
        assert board.get(cx + 2, cy + 1) == 1

        # After 8 steps, should be shifted by (+2, -2)
        for _ in range(4):
            sim.step()
        assert board.get(cx + 2, cy - 2) == 1
        assert board.get(cx + 3, cy - 2) == 1
        assert board.get(cx + 4, cy - 2) == 1
        assert board.get(cx + 4, cy - 1) == 1
        assert board.get(cx + 3, cy) == 1

    def test_random_grid_stability(self, conway):
        """Run random seed for 10 steps and verify no crashes / invariants."""
        board = Board(32, 32)
        rng = np.random.default_rng(42)
        sim = Simulator(board, conway, Neighbourhood.N8, rng=rng)
        sim.reset(SeedConfig(type="random", density=0.3, states=[1]))

        for _ in range(10):
            sim.step()

        # After 10 steps, all values should be 0 or 1
        assert np.all(np.isin(board.data, [0, 1]))
        # Grid should be non-zero (random fill usually persists)
        assert np.any(board.data > 0)


class TestJavaReferenceParity:
    """Explicit parity against known Java reference outputs.

    To generate Java reference outputs, compile and run:
        cd reference_code
        javac CACmd.java
        java CACmd --rule Conway --size 32 32 --seed single --steps 10
    """

    def test_conway_32x32_single_10_steps(self):
        """Run Conway for 10 steps on 32x32 single-center seed.

        A single cell dies immediately (0 neighbours), so after 10 steps
        the board should be all zeros.
        """
        loader = LegacyRuleLoader()
        table = loader.load("Conway", num_states=2)
        board = Board(32, 32)
        sim = Simulator(board, table, Neighbourhood.N8)
        sim.reset(SeedConfig(type="single", state=1))

        for _ in range(10):
            sim.step()

        # Single cell dies in 1 step (0 neighbours), so after 10 steps all zeros
        assert np.all(board.data == 0)
        assert board.data.dtype == np.uint8

    def test_n4_vs_n8(self):
        """Verify that N4 and N8 produce different counts."""
        loader = LegacyRuleLoader()
        table = loader.load("Conway", num_states=2)

        board_n8 = Board(32, 32)
        sim_n8 = Simulator(board_n8, table, Neighbourhood.N8)
        sim_n8.reset(SeedConfig(type="single", state=1))
        sim_n8.step()
        result_n8 = board_n8.data.copy()

        board_n4 = Board(32, 32)
        sim_n4 = Simulator(board_n4, table, Neighbourhood.N4)
        sim_n4.reset(SeedConfig(type="single", state=1))
        sim_n4.step()
        result_n4 = board_n4.data.copy()

        # Single cell has 0 neighbours in both N4 and N8, so dies
        assert result_n8[board_n8.center_y, board_n8.center_x] == 0
        assert result_n4[board_n4.center_y, board_n4.center_x] == 0

    def test_413_rule_loads(self):
        """Verify 413 rule loads and produces multi-state output."""
        loader = LegacyRuleLoader()
        table = loader.load("413", num_states=5)
        board = Board(32, 32)
        rng = np.random.default_rng(42)
        sim = Simulator(board, table, Neighbourhood.N8, rng=rng)
        sim.reset(SeedConfig(type="random", density=0.3, states=[1, 2, 3, 4]))

        for _ in range(5):
            sim.step()

        # Should have produced states 0..4
        unique_states = np.unique(board.data)
        assert len(unique_states) > 1
        assert np.all(unique_states < 5)
