"""Test Pygame renderer and save screenshot for verification."""

import os
import sys
from pathlib import Path

# Set SDL driver to windows (or dummy if unavailable)
os.environ.setdefault("SDL_VIDEODRIVER", "windows")
os.environ["SDL_AUDIODRIVER"] = "dummy"

import numpy as np
import pygame

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ca_engine.core.simulator import Simulator
from ca_engine.core.board import Board
from ca_engine.core.neighbourhood import Neighbourhood
from ca_engine.core.palette import Palette
from ca_engine.core.seed import SeedConfig
from ca_engine.rules.legacy_loader import LegacyRuleLoader
from ca_engine.renderers.pygame_renderer import PygameRenderer


def main() -> None:
    print("Loading Conway rule...")
    loader = LegacyRuleLoader()
    table = loader.load("Conway", num_states=2)

    print("Creating board and simulator...")
    board = Board(64, 64)
    palette = Palette.default(2)
    sim = Simulator(board, table, Neighbourhood.N8, palette)

    # Seed with random pattern
    sim.reset(SeedConfig(type="random", density=0.3, states=[1]))

    print("Initializing Pygame renderer...")
    renderer = PygameRenderer(
        (64, 64),
        palette.colors,
        cell_size=8,
        title="CA Lab — Screenshot Test",
    )

    print("Running 30 steps and saving screenshots...")
    output_dir = Path("screenshots")
    output_dir.mkdir(exist_ok=True)

    for step in range(31):
        action = renderer.render(sim.board.data, sim._collect_metrics())
        if action == "quit":
            break

        # Save every 10 steps
        if step % 10 == 0:
            screenshot_path = output_dir / f"conway_step_{step:03d}.png"
            pygame.image.save(renderer._screen, str(screenshot_path))
            print(f"  Saved: {screenshot_path}")

        sim.step()

    renderer.close()
    print(f"Done! Screenshots saved to: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
