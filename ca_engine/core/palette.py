"""Colour palette management for cell state rendering."""

from __future__ import annotations

from pathlib import Path

import numpy as np


class Palette:
    """A palette mapping state indices to RGB colours.

    Attributes:
        colors: Array of shape (K, 3) with uint8 RGB values.
        num_colors: Number of states (K).
    """

    def __init__(self, colors: np.ndarray) -> None:
        self.colors = colors.astype(np.uint8)
        self.num_colors = len(colors)

    @classmethod
    def from_file(cls, path: str | Path) -> Palette:
        """Load palette from ColourSetup.txt format.

        Format: lines of 'R,G,B #comment' or '#comment' lines.
        Must have at least 2 colors.
        """
        path = Path(path)
        lines = path.read_text().splitlines()

        rgb_list: list[tuple[int, int, int]] = []
        for line in lines:
            # Strip comment
            if "#" in line:
                line = line[: line.index("#")]
            line = line.strip()
            if not line:
                continue

            parts = line.split(",")
            if len(parts) != 3:
                raise ValueError(f"Badly formed colour line: {line!r}")

            r, g, b = int(parts[0].strip()), int(parts[1].strip()), int(parts[2].strip())
            rgb_list.append((r, g, b))

        if len(rgb_list) < 2:
            raise ValueError(f"Must have at least 2 colors, got {len(rgb_list)}")

        colors = np.array(rgb_list, dtype=np.uint8)
        return cls(colors)

    @classmethod
    def default(cls, num_colors: int = 101) -> Palette:
        """Generate default HSB palette.

        State 0 = black, states 1..K-2 = HSB gradient, state K-1 = white.
        """
        colors = np.zeros((num_colors, 3), dtype=np.uint8)
        colors[0] = [0, 0, 0]  # Black
        for i in range(1, num_colors - 1):
            h = (i - 1) / (num_colors - 2) * 0.9
            # HSB to RGB: hue=h, saturation=1.0, brightness=1.0
            rgb = _hsb_to_rgb(h, 1.0, 1.0)
            colors[i] = rgb
        colors[-1] = [255, 255, 255]  # White
        return cls(colors)

    @classmethod
    def grayscale(cls, num_colors: int = 101) -> Palette:
        """Generate grayscale palette.

        State 0 = black, states 1..K-2 = grayscale gradient, state K-1 = white.
        """
        colors = np.zeros((num_colors, 3), dtype=np.uint8)
        colors[0] = [0, 0, 0]
        for i in range(1, num_colors - 1):
            h = (i - 1) / (num_colors - 2) * 0.9
            # Grayscale: brightness only
            v = int(h * 255 / 0.9)
            colors[i] = [v, v, v]
        colors[-1] = [255, 255, 255]
        return cls(colors)

    def __repr__(self) -> str:
        return f"Palette({self.num_colors} colors)"


def _hsb_to_rgb(h: float, s: float, b: float) -> tuple[int, int, int]:
    """Convert HSB/HSV to RGB.

    h in [0, 1], s in [0, 1], b in [0, 1].
    Returns (r, g, b) in [0, 255].
    """
    if s == 0:
        v = int(b * 255)
        return (v, v, v)

    h = h * 6.0
    i = int(h)
    f = h - i
    p = b * (1.0 - s)
    q = b * (1.0 - s * f)
    t = b * (1.0 - s * (1.0 - f))

    rgb_map = [
        (b, t, p),
        (q, b, p),
        (p, b, t),
        (p, q, b),
        (t, p, b),
        (b, p, q),
    ]
    r, g, bval = rgb_map[i % 6]
    return (int(r * 255), int(g * 255), int(bval * 255))
