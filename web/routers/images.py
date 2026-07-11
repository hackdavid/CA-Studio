"""Image upload and quantization API for CA Lab."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from ca_engine.core.image_seed import quantize_image_to_grid

router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    mode: str = "rgb",
    max_states: int = 64,
) -> dict[str, Any]:
    """Upload an image, quantize it to a CA grid, and return metadata.

    Args:
        file: Image file (JPG/PNG/WebP/etc).
        mode: "rgb" or "grayscale".
        max_states: Maximum number of CA states (2–101).

    Returns:
        Dict with grid_data (base64), width, height, num_states,
        unique_colors, thumbnail (base64 PNG), and any error.
    """
    if max_states < 2 or max_states > 101:
        raise HTTPException(status_code=400, detail="max_states must be between 2 and 101")

    if mode not in ("rgb", "grayscale"):
        raise HTTPException(status_code=400, detail="mode must be 'rgb' or 'grayscale'")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    result = quantize_image_to_grid(content, mode=mode, max_states=max_states)

    if result.get("error"):
        return {
            "success": False,
            "error": result["error"],
            "unique_colors": result.get("unique_colors", 0),
            "width": result.get("width", 0),
            "height": result.get("height", 0),
        }

    import base64

    grid = result["grid"]
    grid_data = base64.b64encode(grid.tobytes()).decode("ascii")

    return {
        "success": True,
        "grid_data": grid_data,
        "width": result["width"],
        "height": result["height"],
        "num_states": result["num_states"],
        "unique_colors": result["unique_colors"],
        "thumbnail": result["thumbnail"],
        "palette": result.get("palette") or [],
        "mode": mode,
    }
