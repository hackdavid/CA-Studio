"""Vectorized numpy→PIL frame renderer with metric overlays."""

from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def grid_to_image(
    grid: np.ndarray,
    palette: np.ndarray,
    scale: int = 1,
    metrics: dict[str, Any] | None = None,
    step: int | None = None,
    rule_name: str = "",
    overlay_metrics: bool = False,
    overlay_step: bool = False,
    panel_width: int = 160,
) -> Image.Image:
    """Render a single CA grid frame with optional overlays.

    Args:
        grid: HxW uint8 array.
        palette: Nx3 uint8 array of RGB colors.
        scale: cell size multiplier (1, 2, 4).
        metrics: dict of metric values to display.
        step: current step number.
        rule_name: name of the rule.
        overlay_metrics: if True, draw metrics panel to the right.
        overlay_step: if True, burn step counter into the frame.
        panel_width: width of the metrics sidebar in output pixels.
    """
    h, w = grid.shape
    # Vectorized palette lookup
    safe_grid = np.clip(grid, 0, len(palette) - 1)
    rgb = palette[safe_grid]  # HxWx3

    img = Image.fromarray(rgb, "RGB")
    if scale != 1:
        img = img.resize((w * scale, h * scale), Image.Resampling.NEAREST)

    # If no overlays, return early
    if not overlay_metrics and not overlay_step:
        return img

    # Prepare canvas with optional side panel
    final_w = img.width + (panel_width if overlay_metrics else 0)
    final_h = img.height
    canvas = Image.new("RGB", (final_w, final_h), (15, 23, 42))
    canvas.paste(img, (0, 0))

    draw = ImageDraw.Draw(canvas)

    try:
        font = ImageFont.truetype("arial.ttf", 12)
        font_bold = ImageFont.truetype("arialbd.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
        font_bold = font

    # Metrics panel
    if overlay_metrics:
        _draw_metrics_panel(draw, metrics, step, rule_name, img.width, 0, panel_width, final_h, font, font_bold)

    # Step counter watermark
    if overlay_step:
        text = f"Step {step}" if step is not None else ""
        if text:
            _draw_step_watermark(draw, text, canvas.width, canvas.height, font_bold)

    return canvas


def _draw_metrics_panel(
    draw: ImageDraw.ImageDraw,
    metrics: dict[str, Any] | None,
    step: int | None,
    rule_name: str,
    x: int,
    y: int,
    width: int,
    height: int,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    font_bold: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    """Draw a sidebar panel with metrics."""
    # Background
    draw.rectangle([x, y, x + width, height], fill=(30, 41, 59))
    # Top accent line
    draw.rectangle([x, y, x + width, y + 2], fill=(37, 99, 235))

    pad = 10
    cy = y + pad

    # Title
    draw.text((x + pad, cy), "Metrics", fill=(148, 163, 184), font=font_bold)
    cy += 22

    if rule_name:
        draw.text((x + pad, cy), f"Rule: {rule_name}", fill=(100, 116, 139), font=font)
        cy += 18

    if step is not None:
        draw.text((x + pad, cy), f"Step: {step}", fill=(100, 116, 139), font=font)
        cy += 22

    # Separator
    draw.rectangle([x + pad, cy, x + width - pad, cy + 1], fill=(51, 65, 85))
    cy += 10

    if metrics:
        for key, val in metrics.items():
            if isinstance(val, (int, float, np.floating)):
                val_str = f"{float(val):.4f}"
            else:
                val_str = str(val)
            label = key.replace("_", " ").title()
            draw.text((x + pad, cy), label, fill=(148, 163, 184), font=font)
            draw.text((x + pad, cy + 14), val_str, fill=(255, 255, 255), font=font)
            cy += 36
            if cy > height - 20:
                break


def _draw_step_watermark(
    draw: ImageDraw.ImageDraw,
    text: str,
    canvas_w: int,
    canvas_h: int,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    """Draw a semi-transparent step counter at the bottom right."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = 8
    x1 = canvas_w - tw - margin * 2
    y1 = canvas_h - th - margin * 2 - 4
    x2 = canvas_w - margin
    y2 = canvas_h - margin
    draw.rectangle([x1, y1, x2, y2], fill=(0, 0, 0, 180))
    draw.text((x1 + margin, y1 + 2), text, fill=(255, 255, 255), font=font)
