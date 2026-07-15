"""Background render worker: replay session and capture frames."""

from __future__ import annotations

import asyncio
import io
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from ca_engine.core.board import Board
from ca_engine.core.neighbourhood import Neighbourhood
from ca_engine.core.palette import Palette
from ca_engine.core.seed import SeedConfig
from ca_engine.core.simulator import Simulator
from ca_engine.export.frame_renderer import grid_to_image
from ca_engine.export.video_compiler import compile_gif, compile_mp4, compile_webm
from ca_engine.metrics.dynamic import DynamicMetricFactory
from ca_engine.metrics.registry import MetricRegistry
from ca_engine.rules.yaml_loader import YAMLRuleLoader
from ca_engine.rules.legacy_loader import LegacyRuleLoader

# In-memory job store (replace with DB table in production)
_jobs: dict[str, dict[str, Any]] = {}


def create_job(session_id: int, format: str, start_step: int, end_step: int, scale: int, overlays: dict[str, bool]) -> str:
    """Create a new render job and return its ID."""
    import uuid
    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "id": job_id,
        "session_id": session_id,
        "format": format,
        "start_step": start_step,
        "end_step": end_step,
        "scale": scale,
        "overlays": overlays,
        "status": "queued",
        "progress": 0,
        "result_path": None,
        "error": None,
    }
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    return _jobs.get(job_id)


async def run_render_job(
    job_id: str,
    db_fetcher,
    events_fetcher,
) -> None:
    """Execute a render job asynchronously."""
    job = _jobs.get(job_id)
    if not job:
        return
    job["status"] = "rendering"

    try:
        session_id = job["session_id"]
        start_step = job["start_step"]
        end_step = job["end_step"]
        scale = job["scale"]
        fmt = job["format"]
        overlays = job["overlays"]

        # Load session data from DB
        row = await db_fetcher(session_id)
        if not row:
            raise ValueError("Session not found")

        # Load events for deterministic replay
        events = await events_fetcher(session_id)

        # Build simulator from initial seed (not current grid)
        sim = _build_simulator_from_seed(row)
        rule_name = row.get("rule_name", "")

        # Pre-filter events within our render range
        range_events = [e for e in events if e["step_number"] <= end_step]
        event_idx = 0

        # Fast-forward to start_step
        for step in range(1, start_step + 1):
            # Apply any events at this step
            while event_idx < len(range_events) and range_events[event_idx]["step_number"] == step:
                _apply_event(sim, range_events[event_idx])
                event_idx += 1
            sim.step()

        total_frames = end_step - start_step + 1
        frames: list[Image.Image] = []

        for i in range(total_frames):
            current_step_num = start_step + i + 1
            # Apply events before stepping
            while event_idx < len(range_events) and range_events[event_idx]["step_number"] == current_step_num:
                _apply_event(sim, range_events[event_idx])
                event_idx += 1

            sim.step()
            metrics = sim._collect_metrics()
            img = grid_to_image(
                sim.board.data,
                sim.palette.colors,
                scale=scale,
                metrics=metrics if overlays.get("metrics") else None,
                step=sim.step_num,
                rule_name=rule_name,
                overlay_metrics=overlays.get("metrics", False),
                overlay_step=overlays.get("step", False),
            )
            frames.append(img)
            job["progress"] = int((i + 1) / total_frames * 100)
            # Yield control occasionally
            if i % 10 == 0:
                await asyncio.sleep(0)

        # Compile
        job["status"] = "compiling"
        if fmt == "gif":
            data = compile_gif(frames, fps=10)
            ext = "gif"
        elif fmt == "mp4":
            data = compile_mp4(frames, fps=10)
            ext = "mp4"
        elif fmt == "webm":
            data = compile_webm(frames, fps=10)
            ext = "webm"
        else:
            raise ValueError(f"Unknown format: {fmt}")

        # Save to temp file
        tmp = tempfile.gettempdir()
        out_path = Path(tmp) / f"ca_lab_export_{job_id}.{ext}"
        out_path.write_bytes(data)
        job["result_path"] = str(out_path)
        job["status"] = "done"
        job["progress"] = 100

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)


def _build_simulator_from_seed(row: dict[str, Any]) -> Simulator:
    """Reconstruct simulator from initial seed (deterministic replay)."""
    # Parse rule
    yaml_content = row.get("yaml_content", "")
    num_states = row.get("num_states", 2)
    try:
        loader = YAMLRuleLoader()
        table = loader.parse_content(yaml_content)
    except Exception:
        legacy = LegacyRuleLoader()
        table = legacy.load(row.get("rule_name", "unknown"), num_states)

    board = Board(row.get("board_width", 64), row.get("board_height", 64))
    neighbourhood = Neighbourhood.from_name(row.get("neighbourhood", "moore8"))
    palette = Palette.default(num_states)

    # Always apply seed config for deterministic replay
    seed_cfg = json.loads(row.get("seed_config") or "{}")
    seed = SeedConfig.model_validate(seed_cfg)
    seed.apply(board, np.random.default_rng(seed_cfg.get("seed")))

    sim = Simulator(board, table, neighbourhood, palette)
    return sim


def _apply_event(sim: Simulator, event: dict[str, Any]) -> None:
    """Apply a logged session event to a simulator."""
    action = event.get("action_type", "")
    payload = json.loads(event.get("payload") or "{}")
    if action == "paint":
        try:
            sim.board.set(payload["x"], payload["y"], payload["state"])
        except Exception:
            pass
    elif action == "reset":
        seed_cfg = payload if payload else {}
        if seed_cfg.get("type"):
            sim.reset(SeedConfig.model_validate(seed_cfg))
        else:
            sim.reset()


async def export_session_zip(
    session_row: dict[str, Any],
    snapshots: list[dict[str, Any]],
    metrics_csv: str,
) -> bytes:
    """Generate a session ZIP archive in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Session config JSON
        config = {
            "session_id": session_row.get("id"),
            "name": session_row.get("name"),
            "rule_name": session_row.get("rule_name"),
            "board_width": session_row.get("board_width"),
            "board_height": session_row.get("board_height"),
            "neighbourhood": session_row.get("neighbourhood"),
            "num_states": session_row.get("num_states"),
            "seed_config": json.loads(session_row.get("seed_config") or "{}"),
            "metrics_enabled": json.loads(session_row.get("metrics_enabled") or "[]"),
            "current_step": session_row.get("current_step"),
        }
        zf.writestr("session.json", json.dumps(config, indent=2))

        # Rule YAML
        zf.writestr("rule.yaml", session_row.get("yaml_content", "# rule"))

        # Metrics CSV
        zf.writestr("metrics.csv", metrics_csv)

        # Snapshots as PNGs
        for snap in snapshots:
            grid = np.frombuffer(snap["grid_state"], dtype=np.uint8)
            h, w = config["board_height"], config["board_width"]
            grid = grid.reshape((h, w))
            palette = Palette.default(config["num_states"])
            img = grid_to_image(grid, palette.colors, scale=1)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            zf.writestr(f"snapshots/step_{snap['step_number']}.png", img_bytes.getvalue())

    buf.seek(0)
    return buf.read()
