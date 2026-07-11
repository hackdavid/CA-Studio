"""Image-to-grid quantization service for CA Lab.

Converts uploaded images into CA-initializable grids by reducing
color spectrum to a finite number of discrete states.
"""

from __future__ import annotations

import base64
import io
from typing import Any

import numpy as np
from PIL import Image


def quantize_image_to_grid(
    image_bytes: bytes,
    mode: str = "rgb",
    max_states: int = 64,
    max_dimension: int = 512,
) -> dict[str, Any]:
    """Convert an image to a quantized CA grid.

    Args:
        image_bytes: Raw image file bytes (JPG/PNG/etc).
        mode: "rgb" or "grayscale".
        max_states: Maximum number of CA states to quantize to (2–101).
        max_dimension: Maximum width/height; larger images are downscaled.

    Returns:
        Dict with keys:
            - grid: np.ndarray of shape (H, W) with uint8 state values
            - width: grid width
            - height: grid height
            - num_states: actual number of states used
            - unique_colors: number of unique colors in original image
            - thumbnail: base64-encoded PNG thumbnail of quantized grid
            - error: str or None

    Raises:
        ValueError: If the image has too many unique colors to process.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return {"error": f"Cannot read image: {e}", "grid": None}

    # Convert to appropriate mode
    if mode == "grayscale":
        img = img.convert("L")
        arr = np.array(img, dtype=np.uint8)
    else:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)

    orig_h, orig_w = arr.shape[:2]

    # Resize if too large
    if orig_w > max_dimension or orig_h > max_dimension:
        ratio = min(max_dimension / orig_w, max_dimension / orig_h)
        new_w = int(orig_w * ratio)
        new_h = int(orig_h * ratio)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        arr = np.array(img, dtype=np.uint8)

    h, w = arr.shape[:2]

    # Count unique colors
    if mode == "grayscale":
        unique_colors = int(len(np.unique(arr)))
    else:
        # Flatten RGB to single int per pixel for uniqueness count
        flat = arr.reshape(-1, 3)
        unique_colors = int(len(np.unique(flat, axis=0)))

    # Quantization
    if mode == "grayscale":
        grid, num_states = _quantize_grayscale(arr, max_states)
    else:
        grid, num_states = _quantize_rgb(arr, max_states)

    # Build thumbnail
    thumb = _build_thumbnail(grid, num_states)

    return {
        "grid": grid,
        "width": w,
        "height": h,
        "num_states": num_states,
        "unique_colors": unique_colors,
        "thumbnail": thumb,
        "error": None,
    }


def _quantize_grayscale(arr: np.ndarray, max_states: int) -> tuple[np.ndarray, int]:
    """Quantize grayscale array to K states using uniform binning."""
    # Uniform quantization: divide 0–255 into K bins
    bins = np.linspace(0, 256, max_states + 1, dtype=np.uint16)
    # Digitize returns bin index (1-based), subtract 1 for 0-based
    grid = np.digitize(arr, bins[1:-1]).astype(np.uint8)
    # Remap so the most common state is 1 (alive), background is 0 if appropriate
    # But keep raw for now; states used are 0..max_states-1
    num_states = int(grid.max()) + 1
    return grid, num_states


def _quantize_rgb(arr: np.ndarray, max_states: int) -> tuple[np.ndarray, int]:
    """Quantize RGB array to K states using k-means or uniform method.

    For simplicity and speed we use a hybrid approach:
    1. If unique colors <= max_states, map each unique color to a state directly.
    2. Otherwise, use a simple uniform quantization in RGB space.
    """
    h, w = arr.shape[:2]
    flat = arr.reshape(-1, 3)
    unique = np.unique(flat, axis=0)

    if len(unique) <= max_states:
        # Direct mapping: each unique color → a state
        color_to_state = {tuple(c): i for i, c in enumerate(unique)}
        grid = np.array([color_to_state[tuple(p)] for p in flat], dtype=np.uint8).reshape(h, w)
        return grid, len(unique)

    # Otherwise: uniform quantization per channel
    # Split 0–255 into K^(1/3) bins per channel approximately
    bins_per_channel = max(2, int(np.cbrt(max_states)))
    total_bins = bins_per_channel ** 3
    if total_bins > max_states:
        # Reduce bins_per_channel until we fit
        while bins_per_channel ** 3 > max_states and bins_per_channel > 1:
            bins_per_channel -= 1

    bin_edges = np.linspace(0, 256, bins_per_channel + 1, dtype=np.uint16)
    r_idx = np.digitize(arr[:, :, 0], bin_edges[1:-1])
    g_idx = np.digitize(arr[:, :, 1], bin_edges[1:-1])
    b_idx = np.digitize(arr[:, :, 2], bin_edges[1:-1])

    # Combine into single state index
    grid = (r_idx * (bins_per_channel ** 2) + g_idx * bins_per_channel + b_idx).astype(np.uint8)

    # Remap to contiguous 0..N-1
    unique_states = np.unique(grid)
    state_map = {s: i for i, s in enumerate(unique_states)}
    grid = np.vectorize(state_map.get)(grid).astype(np.uint8)
    num_states = int(grid.max()) + 1
    return grid, num_states


def _build_thumbnail(grid: np.ndarray, num_states: int) -> str:
    """Create a small base64 PNG thumbnail of the quantized grid."""
    h, w = grid.shape
    # Scale up for visibility if small
    scale = max(1, min(4, 256 // max(h, w)))
    thumb = np.repeat(np.repeat(grid, scale, axis=0), scale, axis=1)

    # Simple colormap: state 0 = white (background), others = distinct colors
    thumb_rgb = np.zeros((thumb.shape[0], thumb.shape[1], 3), dtype=np.uint8)
    for s in range(num_states):
        if s == 0:
            # Background state: light gray so grid structure is visible
            r, g, b = 240, 240, 240
        else:
            # Spread hues across the color wheel, skip red-heavy region near 0
            hue = ((s - 1) / max(num_states - 1, 1)) * 360
            # Shift so state 1 starts near cyan/blue rather than red
            hue = (hue + 180) % 360
            r, g, b = _hsv_to_rgb(hue, 0.75, 0.9)
        thumb_rgb[thumb == s] = [r, g, b]

    img = Image.fromarray(thumb_rgb, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    """Simple HSV to RGB conversion."""
    import math

    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c

    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    return (
        int((r + m) * 255),
        int((g + m) * 255),
        int((b + m) * 255),
    )


def grid_to_base64(grid: np.ndarray) -> str:
    """Encode a uint8 grid to base64 string."""
    return base64.b64encode(grid.tobytes()).decode("ascii")


def base64_to_grid(data: str, width: int, height: int) -> np.ndarray:
    """Decode a base64 string back to a uint8 grid."""
    raw = base64.b64decode(data)
    return np.frombuffer(raw, dtype=np.uint8).reshape((height, width))
