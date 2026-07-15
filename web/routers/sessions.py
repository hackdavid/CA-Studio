"""Session CRUD API routes."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException

from ca_engine.core.board import Board
from ca_engine.core.seed import SeedConfig, SeedType
from web.database import get_db
from web.models import SessionCreate, SessionOut, SessionUpdate, SnapshotOut

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _normalize_seed_config(seed_config: dict[str, Any]) -> dict[str, Any]:
    """Map dashboard seed keys to SeedConfig fields."""
    config = dict(seed_config or {})
    if "mode" in config and "type" not in config:
        mode = config.pop("mode")
        if mode == "center":
            config["type"] = SeedType.SINGLE
            config.setdefault("state", 1)
            config.setdefault("position", "center")
        elif mode == "empty":
            config["type"] = "empty"
        else:
            config["type"] = mode
    return config


def _build_initial_grid(
    width: int,
    height: int,
    num_states: int,
    seed_config: dict[str, Any],
) -> bytes:
    """Apply seed configuration and return grid bytes."""
    board = Board(width, height)
    config = _normalize_seed_config(seed_config)
    seed_type = config.get("type", SeedType.SINGLE)

    if seed_type == "empty":
        return board.data.tobytes()

    if seed_type == SeedType.RANDOM:
        states = config.get("states")
        if not states:
            states = list(range(1, num_states))
        config["states"] = states

    seed = SeedConfig.model_validate(config)
    seed.apply(board, np.random.default_rng())
    return board.data.tobytes()


@router.get("/", response_model=list[SessionOut])
async def list_sessions() -> list[dict[str, Any]]:
    """List all sessions."""
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT s.id, s.name, s.rule_id, r.name as rule_name, s.board_width, s.board_height,
                   s.neighbourhood, s.num_states, s.seed_config, s.current_step, s.status,
                   s.metrics_enabled, s.mode, s.created_at
            FROM sessions s
            JOIN rules r ON s.rule_id = r.id
            ORDER BY s.updated_at DESC
        """)
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["seed_config"] = json.loads(d["seed_config"] or "{}")
            d["metrics_enabled"] = json.loads(d["metrics_enabled"] or "[]")
            result.append(d)
        return result
    finally:
        await db.close()


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: int) -> dict[str, Any]:
    """Get a single session by ID."""
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT s.id, s.name, s.rule_id, r.name as rule_name, s.board_width, s.board_height,
                   s.neighbourhood, s.num_states, s.seed_config, s.current_step, s.status,
                   s.metrics_enabled, s.mode, s.created_at
            FROM sessions s
            JOIN rules r ON s.rule_id = r.id
            WHERE s.id = ?
        """, (session_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        d = dict(row)
        d["seed_config"] = json.loads(d["seed_config"] or "{}")
        d["metrics_enabled"] = json.loads(d["metrics_enabled"] or "[]")
        # Load evolution config if applicable
        if d.get("mode") == "evolve":
            cur2 = await db.execute(
                """SELECT * FROM evolution_configs WHERE session_id = ?""",
                (session_id,),
            )
            eco = await cur2.fetchone()
            if eco:
                d["evolution_config"] = {
                    "id": eco["id"],
                    "session_id": eco["session_id"],
                    "fitness_weights": json.loads(eco["fitness_weights_json"] or "{}"),
                    "population_size": eco["population_size"],
                    "generations": eco["generations"],
                    "mutation_rate": eco["mutation_rate"],
                    "evolve_rule": bool(eco["evolve_rule"]),
                    "evolve_seed": bool(eco["evolve_seed"]),
                    "constraints": json.loads(eco["constraints_json"] or "{}"),
                    "current_generation": eco["current_generation"],
                    "best_fitness": eco["best_fitness"],
                }
            else:
                d["evolution_config"] = None
        return d
    finally:
        await db.close()


@router.post("/", response_model=SessionOut)
async def create_session(session: SessionCreate) -> dict[str, Any]:
    """Create a new session."""
    from web.services.metric_loader import validate_metric_names

    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM rules WHERE id = ?", (session.rule_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"Rule id {session.rule_id} not found")

        invalid_metrics = await validate_metric_names(session.metrics_enabled)
        if invalid_metrics:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown metrics: {', '.join(invalid_metrics)}",
            )

        cursor = await db.execute(
            """INSERT INTO sessions (name, rule_id, board_width, board_height, neighbourhood,
                num_states, seed_config, metrics_enabled, mode)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session.name,
                session.rule_id,
                session.board_width,
                session.board_height,
                session.neighbourhood,
                session.num_states,
                json.dumps(session.seed_config),
                json.dumps(session.metrics_enabled),
                session.mode,
            ),
        )
        await db.commit()
        session_id = cursor.lastrowid

        grid_bytes = _build_initial_grid(
            session.board_width,
            session.board_height,
            session.num_states,
            session.seed_config,
        )
        await db.execute(
            "UPDATE sessions SET current_grid = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (grid_bytes, session_id),
        )
        await db.commit()

        # Insert evolution config if provided
        if session.mode == "evolve" and session.evolution_config:
            cfg = session.evolution_config
            target_image = None
            if cfg.target_image_base64:
                import base64
                try:
                    target_image = base64.b64decode(cfg.target_image_base64)
                except Exception:
                    pass
            await db.execute(
                """INSERT INTO evolution_configs
                   (session_id, target_image, fitness_weights_json, population_size,
                    generations, mutation_rate, evolve_rule, evolve_seed, constraints_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    target_image,
                    json.dumps(cfg.fitness_weights),
                    cfg.population_size,
                    cfg.generations,
                    cfg.mutation_rate,
                    cfg.evolve_rule,
                    cfg.evolve_seed,
                    json.dumps(cfg.constraints),
                ),
            )
            await db.commit()

        return await get_session(session_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await db.close()


@router.put("/{session_id}", response_model=SessionOut)
async def update_session(session_id: int, session: SessionUpdate) -> dict[str, Any]:
    """Update session state."""
    db = await get_db()
    try:
        fields = []
        values = []

        if session.name is not None:
            fields.append("name = ?")
            values.append(session.name)
        if session.current_step is not None:
            fields.append("current_step = ?")
            values.append(session.current_step)
        if session.status is not None:
            fields.append("status = ?")
            values.append(session.status)
        if session.current_grid is not None:
            # Convert 2D list to bytes
            grid_array = np.array(session.current_grid, dtype=np.uint8)
            fields.append("current_grid = ?")
            values.append(grid_array.tobytes())

        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(session_id)

        await db.execute(
            f"UPDATE sessions SET {', '.join(fields)} WHERE id = ?",
            values,
        )
        await db.commit()
        return await get_session(session_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await db.close()


@router.delete("/{session_id}")
async def delete_session(session_id: int) -> dict[str, str]:
    """Delete a session and all its snapshots."""
    db = await get_db()
    try:
        await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        await db.commit()
        return {"message": "Session deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await db.close()


@router.post("/{session_id}/snapshots")
async def save_snapshot(session_id: int, step: int, grid: list[list[int]], metrics: dict[str, Any]) -> dict[str, Any]:
    """Save a snapshot of the current simulation state."""
    db = await get_db()
    try:
        grid_array = np.array(grid, dtype=np.uint8)
        cursor = await db.execute(
            """INSERT INTO session_snapshots (session_id, step_number, grid_state, metrics_json)
               VALUES (?, ?, ?, ?)""",
            (session_id, step, grid_array.tobytes(), json.dumps(metrics)),
        )
        await db.commit()
        snapshot_id = cursor.lastrowid
        return {"id": snapshot_id, "session_id": session_id, "step_number": step}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await db.close()


@router.get("/{session_id}/snapshots", response_model=list[SnapshotOut])
async def list_snapshots(session_id: int) -> list[dict[str, Any]]:
    """List all snapshots for a session."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, session_id, step_number, metrics_json, created_at FROM session_snapshots WHERE session_id = ? ORDER BY step_number",
            (session_id,),
        )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["metrics_json"] = json.loads(d["metrics_json"] or "{}")
            result.append(d)
        return result
    finally:
        await db.close()


@router.get("/{session_id}/snapshots/{step_number}")
async def get_snapshot(session_id: int, step_number: int) -> dict[str, Any]:
    """Get a specific snapshot by step number."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM session_snapshots WHERE session_id = ? AND step_number = ?",
            (session_id, step_number),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Snapshot not found")
        d = dict(row)
        d["metrics_json"] = json.loads(d["metrics_json"] or "{}")
        d["grid_state"] = list(np.frombuffer(d["grid_state"], dtype=np.uint8))
        return d
    finally:
        await db.close()


@router.get("/{session_id}/export.png")
async def export_session_image(session_id: int) -> Any:
    """Export the current grid as a PNG using the original image seed palette."""
    import io
    from fastapi.responses import StreamingResponse
    from PIL import Image

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT board_width, board_height, num_states, seed_config, current_grid FROM sessions WHERE id = ?",
            (session_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")

        d = dict(row)
        w = d["board_width"]
        h = d["board_height"]
        num_states = d["num_states"]
        seed_config = json.loads(d["seed_config"] or "{}")
        grid_bytes = d["current_grid"]

        if not grid_bytes:
            raise HTTPException(status_code=400, detail="No grid data available")

        grid = np.frombuffer(grid_bytes, dtype=np.uint8).reshape((h, w))

        # Build palette: use image seed palette if available, else fallback
        palette = seed_config.get("palette")
        if palette and len(palette) >= num_states:
            rgb = np.zeros((h, w, 3), dtype=np.uint8)
            for s in range(min(len(palette), num_states)):
                rgb[grid == s] = palette[s]
        else:
            # Fallback: grayscale
            rgb = np.stack([grid, grid, grid], axis=-1)

        img = Image.fromarray(rgb, "RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        return StreamingResponse(buf, media_type="image/png")
    finally:
        await db.close()


@router.get("/{session_id}/grid")
async def get_grid(session_id: int) -> dict[str, Any]:
    """Get the current grid state as a 2D array."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT current_grid, board_width, board_height FROM sessions WHERE id = ?",
            (session_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")

        if row["current_grid"] is None:
            return {"grid": None, "width": row["board_width"], "height": row["board_height"]}

        grid = np.frombuffer(row["current_grid"], dtype=np.uint8)
        grid = grid.reshape((row["board_height"], row["board_width"]))
        return {"grid": grid.tolist(), "width": row["board_width"], "height": row["board_height"]}
    finally:
        await db.close()
