"""Pygame renderer for desktop real-time visualization."""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import Renderer

# Pygame is an optional dependency
# We import it lazily to avoid hard dependency
try:
    import pygame

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    pygame = None  # type: ignore


class PygameRenderer(Renderer):
    """Real-time Pygame window renderer.

    Controls:
        Space: pause/resume
        S: single step
        R: reset
        C: toggle color/grayscale
        Click: paint cell
        Escape / Q: quit
        Arrow keys: speed up/down
    """

    def __init__(
        self,
        grid_shape: tuple[int, int],
        palette: np.ndarray,
        cell_size: int = 4,
        title: str = "CA Lab",
        show_grid: bool = True,
    ) -> None:
        if not PYGAME_AVAILABLE:
            raise ImportError("Pygame is required for PygameRenderer. Install with: pip install pygame")

        super().__init__()
        self._palette = palette.astype(np.uint8)
        self._cell_size = cell_size
        self._grid_shape = grid_shape
        self._paused = False
        self._step_request = False
        self._reset_request = False
        self._speed = 30  # target FPS
        self._running = True
        self._title = title
        self._grayscale = False
        self._show_grid = show_grid
        self._grid_color = (80, 80, 80)  # Dark gray grid lines

        # Pygame init
        pygame.init()
        self._screen = pygame.display.set_mode(
            (grid_shape[1] * cell_size, grid_shape[0] * cell_size)
        )
        pygame.display.set_caption(title)
        self._clock = pygame.time.Clock()
        self._font = pygame.font.SysFont("monospace", 14)

    @property
    def name(self) -> str:
        return "pygame"

    @property
    def is_live(self) -> bool:
        return True

    def render(self, grid: np.ndarray, metrics: dict[str, Any] | None = None) -> str:
        """Render one frame and handle events.

        Returns:
            Action string: "continue", "pause", "step", "reset", "quit".
        """
        self._handle_events()

        if self._reset_request:
            self._reset_request = False
            return "reset"

        if self._step_request:
            self._step_request = False
            return "step"

        if self._paused:
            return "pause"

        if not self._running:
            return "quit"

        # Convert grid to RGB
        colors = self._palette[grid]
        if self._grayscale:
            # Simple grayscale: average RGB
            gray = colors.mean(axis=2).astype(np.uint8)
            colors = np.stack([gray, gray, gray], axis=2)

        # Create surface from RGB array
        surface = pygame.surfarray.make_surface(colors)
        if self._cell_size > 1:
            surface = pygame.transform.scale(
                surface,
                (self._grid_shape[1] * self._cell_size, self._grid_shape[0] * self._cell_size),
            )

        self._screen.blit(surface, (0, 0))

        # Draw grid lines (optional)
        if self._show_grid and self._cell_size >= 4:
            self._draw_grid_lines()

        # Draw metrics overlay
        if metrics:
            self._draw_metrics(metrics)

        # Draw status overlay
        status = f"FPS: {int(self._clock.get_fps())}"
        if self._paused:
            status += " [PAUSED]"
        if self._show_grid:
            status += " [GRID]"
        text = self._font.render(status, True, (255, 255, 255))
        self._screen.blit(text, (5, 5))

        pygame.display.flip()
        self._clock.tick(self._speed)

        return "continue"

    def _handle_events(self) -> None:
        """Poll Pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self._paused = not self._paused
                elif event.key == pygame.K_s:
                    self._step_request = True
                elif event.key == pygame.K_r:
                    self._reset_request = True
                elif event.key == pygame.K_c:
                    self._grayscale = not self._grayscale
                elif event.key == pygame.K_g:
                    self._show_grid = not self._show_grid
                elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    self._running = False
                elif event.key == pygame.K_UP:
                    self._speed = min(120, self._speed + 5)
                elif event.key == pygame.K_DOWN:
                    self._speed = max(5, self._speed - 5)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    x, y = event.pos
                    grid_x = x // self._cell_size
                    grid_y = y // self._cell_size
                    self._paint_cell = (grid_x, grid_y)

    def _draw_grid_lines(self) -> None:
        """Draw grid lines between cells."""
        h, w = self._grid_shape
        cs = self._cell_size
        # Vertical lines
        for x in range(0, w * cs + 1, cs):
            pygame.draw.line(self._screen, self._grid_color, (x, 0), (x, h * cs), 1)
        # Horizontal lines
        for y in range(0, h * cs + 1, cs):
            pygame.draw.line(self._screen, self._grid_color, (0, y), (w * cs, y), 1)

    def _draw_metrics(self, metrics: dict[str, Any]) -> None:
        """Draw metrics text on screen."""
        y_offset = 25
        for key, value in metrics.items():
            text = self._font.render(f"{key}: {value:.4f}", True, (255, 255, 255))
            self._screen.blit(text, (5, y_offset))
            y_offset += 16

    def run(self, simulator: Any) -> None:
        """Blocking event loop.

        Args:
            simulator: Simulator instance with .step(), .reset(), .board, .metrics.
        """
        while self._running:
            action = self.render(simulator.board.data, simulator._collect_metrics())

            if action == "quit":
                break
            elif action == "reset":
                simulator.reset()
            elif action == "step":
                simulator.step()
            elif action == "pause":
                # Still render but don't step
                pass
            else:
                simulator.step()

        self.close()

    def close(self) -> None:
        """Clean up Pygame."""
        if PYGAME_AVAILABLE:
            pygame.quit()

    def set_palette(self, palette: np.ndarray) -> None:
        """Update the color palette."""
        self._palette = palette.astype(np.uint8)

    def __repr__(self) -> str:
        return f"PygameRenderer({self._grid_shape[1]}x{self._grid_shape[0]}, cell_size={self._cell_size})"
