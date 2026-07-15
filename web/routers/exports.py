"""Export API routes: PNG, GIF/MP4/WebM renders, ZIP, CLI state, metrics CSV."""

from __future__ import annotations

import asyncio
import base64
import csv
import io
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml
import asyncio

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from ca_engine.core.palette import Palette
from ca_engine.export.frame_renderer import grid_to_image
from ca_engine.export.render_worker import (
    create_job,
    export_session_zip,
    get_job,
    run_render_job,
)
from web.database import get_db
from web.models import CliStateExport, ExportJobOut, RenderRequest

router = APIRouter(prefix="/api/export", tags=["exports"])


# ─── Helpers ────────────────────────────────────────────────────────────────

async def _fetch_session_row(session_id: int) -> dict[str, Any]:
    """Fetch session joined with rule."""
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT s.id, s.name, s.rule_id, r.name as rule_name, s.board_width, s.board_height,
                   s.neighbourhood, s.num_states, s.seed_config, s.current_step, s.status,
                   s.metrics_enabled, s.current_grid, r.yaml_content, s.created_at
            FROM sessions s
            JOIN rules r ON s.rule_id = r.id
            WHERE s.id = ?
        """, (session_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        return dict(row)
    finally:
        await db.close()


async def _fetch_snapshots(session_id: int) -> list[dict[str, Any]]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM session_snapshots WHERE session_id = ? ORDER BY step_number",
            (session_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def _insert_event(session_id: int, step: int, action: str, payload: dict[str, Any]) -> None:
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO session_events (session_id, step_number, action_type, payload) VALUES (?, ?, ?, ?)",
            (session_id, step, action, json.dumps(payload)),
        )
        await db.commit()
    finally:
        await db.close()


# ─── Instant PNG Export ─────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/png")
async def export_png(session_id: int, overlay_metrics: bool = False, overlay_step: bool = True) -> StreamingResponse:
    """Export current session grid as PNG (instant)."""
    row = await _fetch_session_row(session_id)
    grid_bytes = row.get("current_grid")
    if not grid_bytes:
        raise HTTPException(status_code=400, detail="No grid data available")

    h, w = row["board_height"], row["board_width"]
    grid = np.frombuffer(grid_bytes, dtype=np.uint8).reshape((h, w))
    palette = Palette.default(row["num_states"])

    # Simple metrics collection (no simulator needed for static export)
    metrics = {}
    non_zero = np.count_nonzero(grid)
    metrics["density"] = float(non_zero / grid.size)

    img = grid_to_image(
        grid,
        palette.colors,
        scale=1,
        metrics=metrics if overlay_metrics else None,
        step=row.get("current_step"),
        rule_name=row.get("rule_name", ""),
        overlay_metrics=overlay_metrics,
        overlay_step=overlay_step,
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


# ─── Metrics CSV ────────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/metrics-csv")
async def export_metrics_csv(session_id: int) -> StreamingResponse:
    """Export session snapshots metrics as CSV."""
    snapshots = await _fetch_snapshots(session_id)
    if not snapshots:
        raise HTTPException(status_code=404, detail="No snapshots found")

    output = io.StringIO()
    writer = csv.writer(output)
    all_keys: set[str] = set()
    parsed: list[dict[str, Any]] = []
    for snap in snapshots:
        d = dict(snap)
        metrics = json.loads(d.get("metrics_json") or "{}")
        d["metrics"] = metrics
        all_keys.update(metrics.keys())
        parsed.append(d)

    headers = ["step_number", "created_at"] + sorted(all_keys)
    writer.writerow(headers)
    for p in parsed:
        row = [p["step_number"], p.get("created_at", "")]
        for k in sorted(all_keys):
            row.append(p["metrics"].get(k, ""))
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode()), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=session_{session_id}_metrics.csv"})


# ─── CLI State Export ───────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/cli-state")
async def export_cli_state(session_id: int, body: CliStateExport | None = None) -> StreamingResponse:
    """Export a self-contained CLI resume package."""
    row = await _fetch_session_row(session_id)
    grid_bytes = row.get("current_grid")
    if not grid_bytes:
        raise HTTPException(status_code=400, detail="No grid data available")

    include_snapshots = body.include_snapshots if body else False

    resume = {
        "name": f"resume-{row['name']}",
        "rule": row["rule_name"],
        "width": row["board_width"],
        "height": row["board_height"],
        "num_states": row["num_states"],
        "neighbourhood": row["neighbourhood"],
        "metrics": json.loads(row.get("metrics_enabled") or "[]"),
        "seed": {
            "type": "resume",
            "grid_base64": base64.b64encode(grid_bytes).decode(),
            "step": row.get("current_step", 0),
        },
        "palette": None,
        "steps": 100,
        "renderer": "headless",
        "log": {"enabled": True, "output_dir": "./results", "format": "csv", "metrics_every": 1},
        "_rule_yaml": row.get("yaml_content", ""),
        "_session_id": row["id"],
    }

    buf = io.BytesIO()
    with io.BytesIO() as inner:
        import zipfile
        with zipfile.ZipFile(inner, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("resume.yaml", yaml.dump(resume, sort_keys=False))
            zf.writestr("rule.yaml", row.get("yaml_content", "# rule"))
            zf.writestr("session.json", json.dumps({
                "id": row["id"],
                "name": row["name"],
                "current_step": row.get("current_step"),
                "seed_config": json.loads(row.get("seed_config") or "{}"),
            }, indent=2))
            if include_snapshots:
                snaps = await _fetch_snapshots(session_id)
                for snap in snaps:
                    zf.writestr(f"snapshots/step_{snap['step_number']}.bin", snap["grid_state"])
        inner.seek(0)
        buf.write(inner.read())

    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip", headers={"Content-Disposition": f"attachment; filename=session_{session_id}_cli_resume.zip"})


# ─── Render Job (GIF / MP4 / WebM) ────────────────────────────────────────────

@router.post("/sessions/{session_id}/render")
async def start_render(session_id: int, req: RenderRequest, background_tasks: BackgroundTasks) -> ExportJobOut:
    """Queue a background render job for GIF/MP4/WebM."""
    # Validate session exists
    await _fetch_session_row(session_id)

    job_id = create_job(
        session_id=session_id,
        format=req.format,
        start_step=req.start_step,
        end_step=req.end_step,
        scale=req.scale,
        overlays={"metrics": req.overlay_metrics, "step": req.overlay_step},
    )

    # Persist job to DB
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO export_jobs
               (id, session_id, format, start_step, end_step, scale, overlay_metrics, overlay_step, status, progress)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (job_id, session_id, req.format, req.start_step, req.end_step, req.scale,
             req.overlay_metrics, req.overlay_step, "queued", 0),
        )
        await db.commit()
    finally:
        await db.close()

    def run_job_sync() -> None:
        """Sync wrapper for background task execution."""
        async def db_fetcher(sid: int) -> dict[str, Any]:
            return await _fetch_session_row(sid)

        async def events_fetcher(sid: int) -> list[dict[str, Any]]:
            db = await get_db()
            try:
                cursor = await db.execute(
                    "SELECT * FROM session_events WHERE session_id = ? ORDER BY step_number",
                    (sid,),
                )
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
            finally:
                await db.close()

        asyncio.run(run_render_job(job_id, db_fetcher, events_fetcher))

    # Launch background render via BackgroundTasks (thread pool)
    background_tasks.add_task(run_job_sync)

    job = get_job(job_id)
    return ExportJobOut(
        id=job["id"],
        session_id=job["session_id"],
        format=job["format"],
        start_step=job["start_step"],
        end_step=job["end_step"],
        scale=job["scale"],
        status=job["status"],
        progress=job["progress"],
    )


@router.get("/jobs/{job_id}")
async def get_export_job(job_id: str) -> ExportJobOut:
    """Poll render job status."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM export_jobs WHERE id = ?", (job_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        d = dict(row)
        return ExportJobOut(
            id=d["id"],
            session_id=d["session_id"],
            format=d["format"],
            start_step=d["start_step"],
            end_step=d["end_step"],
            scale=d["scale"],
            status=d["status"],
            progress=d["progress"],
            error=d.get("error"),
            created_at=str(d["created_at"]) if d.get("created_at") else None,
        )
    finally:
        await db.close()


@router.get("/jobs/{job_id}/download")
async def download_render(job_id: str) -> FileResponse:
    """Download completed render file."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=400, detail=f"Job status is {job['status']}")
    path = job.get("result_path")
    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="Result file missing")
    media_type = {
        "gif": "image/gif",
        "mp4": "video/mp4",
        "webm": "video/webm",
    }.get(job["format"], "application/octet-stream")
    return FileResponse(path, media_type=media_type, filename=f"session_{job['session_id']}_render.{job['format']}")


# ─── Session ZIP ────────────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/zip")
async def export_session_zip_endpoint(session_id: int) -> StreamingResponse:
    """Export full session archive as ZIP."""
    row = await _fetch_session_row(session_id)
    snapshots = await _fetch_snapshots(session_id)

    # Build metrics CSV string
    output = io.StringIO()
    writer = csv.writer(output)
    all_keys: set[str] = set()
    parsed: list[dict[str, Any]] = []
    for snap in snapshots:
        d = dict(snap)
        metrics = json.loads(d.get("metrics_json") or "{}")
        d["metrics"] = metrics
        all_keys.update(metrics.keys())
        parsed.append(d)
    headers = ["step_number", "created_at"] + sorted(all_keys)
    writer.writerow(headers)
    for p in parsed:
        rw = [p["step_number"], p.get("created_at", "")]
        for k in sorted(all_keys):
            rw.append(p["metrics"].get(k, ""))
        writer.writerow(rw)
    csv_str = output.getvalue()

    zip_bytes = await export_session_zip(row, snapshots, csv_str)
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=session_{session_id}_archive.zip"},
    )
