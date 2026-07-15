"""Compile frames into GIF, MP4, or WebM using imageio."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path
from typing import Any

import imageio
import numpy as np
from PIL import Image


def compile_gif(frames: list[Image.Image], fps: int = 10) -> bytes:
    """Compile PIL frames into an optimized GIF."""
    buf = io.BytesIO()
    np_frames = [np.array(f.convert("RGB")) for f in frames]
    imageio.mimsave(buf, np_frames, format="GIF", fps=fps, loop=0, quantizer=2, palettesize=256)
    buf.seek(0)
    return buf.read()


def compile_mp4(frames: list[Image.Image], fps: int = 10) -> bytes:
    """Compile PIL frames into an MP4 via imageio-ffmpeg (requires temp file)."""
    np_frames = [np.array(f.convert("RGB")) for f in frames]
    tmp = tempfile.mktemp(suffix=".mp4")
    try:
        writer = imageio.get_writer(tmp, format="FFMPEG", mode="I", fps=fps, codec="libx264", quality=8)
        for fr in np_frames:
            writer.append_data(fr)
        writer.close()
        data = Path(tmp).read_bytes()
    finally:
        Path(tmp).unlink(missing_ok=True)
    return data


def compile_webm(frames: list[Image.Image], fps: int = 10) -> bytes:
    """Compile PIL frames into a WebM via imageio-ffmpeg (requires temp file)."""
    np_frames = [np.array(f.convert("RGB")) for f in frames]
    tmp = tempfile.mktemp(suffix=".webm")
    try:
        writer = imageio.get_writer(tmp, format="FFMPEG", mode="I", fps=fps, codec="libvpx", quality=8)
        for fr in np_frames:
            writer.append_data(fr)
        writer.close()
        data = Path(tmp).read_bytes()
    finally:
        Path(tmp).unlink(missing_ok=True)
    return data
