"""WebSocket simulation endpoint.

Manages real-time CA simulation over WebSocket with play/pause/step controls.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from web.database import get_db
from ca_engine.core.simulator import Simulator
from ca_engine.core.board import Board
from ca_engine.core.neighbourhood import Neighbourhood
from ca_engine.core.palette import Palette
from ca_engine.metrics.dynamic import DynamicMetricFactory
from ca_engine.metrics.registry import MetricRegistry
from ca_engine.rules.yaml_loader import YAMLRuleLoader
from ca_engine.rules.legacy_loader import LegacyRuleLoader
from web.routers.sessions import _build_initial_grid
from web.services.metric_loader import fetch_all_custom_metrics

router = APIRouter(prefix="/api/sim", tags=["simulations"])

# Active simulation tasks
active_simulations: dict[int, asyncio.Task] = {}


async def _load_simulator(session_id: int) -> Simulator:
    """Load simulator from session data."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT s.rule_id, s.board_width, s.board_height, s.neighbourhood,
                      s.num_states, s.seed_config, s.current_grid, s.current_step,
                      s.metrics_enabled, r.yaml_content, r.name as rule_name
               FROM sessions s
               JOIN rules r ON s.rule_id = r.id
               WHERE s.id = ?""",
            (session_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise ValueError(f"Session {session_id} not found")

        # Load rule from YAML
        try:
            loader = YAMLRuleLoader()
            table = loader.parse_content(row["yaml_content"])
        except Exception:
            # Fallback to legacy loader
            legacy = LegacyRuleLoader()
            table = legacy.load(row["rule_name"], row["num_states"])

        board = Board(row["board_width"], row["board_height"])
        neighbourhood = Neighbourhood.from_name(row["neighbourhood"])
        palette = Palette.default(row["num_states"])

        # Load grid if available, otherwise apply seed config
        if row["current_grid"]:
            grid = np.frombuffer(row["current_grid"], dtype=np.uint8)
            board.data = grid.reshape((row["board_height"], row["board_width"]))
        else:
            seed_config = json.loads(row["seed_config"] or "{}")
            grid_bytes = _build_initial_grid(
                row["board_width"],
                row["board_height"],
                row["num_states"],
                seed_config,
            )
            board.data = np.frombuffer(grid_bytes, dtype=np.uint8).reshape(
                (row["board_height"], row["board_width"])
            )

        sim = Simulator(board, table, neighbourhood, palette)
        sim.step_num = row["current_step"] or 0

        # Attach metrics
        metrics_enabled = json.loads(row["metrics_enabled"] or "[]")
        registry = MetricRegistry()
        custom_metrics = await fetch_all_custom_metrics()
        for metric_name in metrics_enabled:
            custom_row = custom_metrics.get(metric_name)
            try:
                metric = DynamicMetricFactory.resolve_metric(metric_name, registry, custom_row)
                metric.on_init((row["board_height"], row["board_width"]), row["num_states"])
                sim.attach_metric(metric)
            except KeyError as e:
                raise ValueError(str(e)) from e

        return sim
    finally:
        await db.close()


async def _save_session_state(session_id: int, sim: Simulator) -> None:
    """Save current simulation state to database."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE sessions SET current_grid = ?, current_step = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (sim.board.data.tobytes(), sim.step_num, session_id),
        )
        await db.commit()
    finally:
        await db.close()


@router.websocket("/ws/{session_id}")
async def simulation_websocket(websocket: WebSocket, session_id: int) -> None:
    """WebSocket endpoint for real-time simulation.

    Protocol:
      Client → Server: JSON commands
      Server → Client: JSON status + binary (msgpack) frame data
    """
    await websocket.accept()

    try:
        sim = await _load_simulator(session_id)
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
        return

    running = False
    fps = 10
    task: asyncio.Task | None = None

    async def send_frame() -> None:
        """Send current state to client."""
        grid = sim.board.data
        metrics = sim._collect_metrics()

        # Send palette + grid as binary
        # First send metadata JSON
        await websocket.send_json({
            "type": "frame",
            "step": sim.step_num,
            "metrics": metrics,
            "grid_shape": grid.shape,
            "palette": Palette.default(sim.board.data.max() + 1).colors.tolist(),
        })
        # Then send raw grid bytes
        await websocket.send_bytes(grid.tobytes())

    async def simulation_loop() -> None:
        """Background simulation loop."""
        nonlocal running
        while running:
            sim.step()
            await send_frame()
            await _save_session_state(session_id, sim)
            await asyncio.sleep(1.0 / fps)

    # Send initial state
    await send_frame()

    try:
        while True:
            msg = await websocket.receive_json()
            action = msg.get("action")

            if action == "start":
                grid = msg.get("grid")
                if grid is not None:
                    arr = np.array(grid, dtype=np.uint8)
                    h, w = sim.board.data.shape
                    if arr.size == h * w:
                        sim.board.data = arr.reshape((h, w))
                        sim.step_num = 0
                        await _save_session_state(session_id, sim)
                        await send_frame()
                if not running:
                    running = True
                    task = asyncio.create_task(simulation_loop())
                await websocket.send_json({"type": "status", "status": "running", "fps": fps})

            elif action == "pause":
                running = False
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                await _save_session_state(session_id, sim)
                await websocket.send_json({"type": "status", "status": "paused"})

            elif action == "stop":
                running = False
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                sim.reset()
                await _save_session_state(session_id, sim)
                await send_frame()
                await websocket.send_json({"type": "status", "status": "stopped"})

            elif action == "step":
                count = msg.get("count", 1)
                for _ in range(count):
                    sim.step()
                await _save_session_state(session_id, sim)
                await send_frame()
                await websocket.send_json({"type": "status", "status": "paused", "step": sim.step_num})

            elif action == "reset":
                sim.reset()
                await _save_session_state(session_id, sim)
                await send_frame()
                await websocket.send_json({"type": "status", "status": "stopped", "step": 0})

            elif action == "paint":
                x = msg.get("x", 0)
                y = msg.get("y", 0)
                state = msg.get("state", 1)
                try:
                    sim.board.set(x, y, state)
                    await _save_session_state(session_id, sim)
                    # Recalculate metrics and send lightweight update
                    metrics = sim._collect_metrics()
                    await websocket.send_json({
                        "type": "metrics",
                        "step": sim.step_num,
                        "metrics": metrics,
                    })
                except Exception as paint_err:
                    await websocket.send_json({"type": "error", "message": str(paint_err)})

            elif action == "speed":
                fps = max(1, min(60, msg.get("fps", 10)))
                await websocket.send_json({"type": "status", "status": "running" if running else "paused", "fps": fps})

            elif action == "snapshot":
                await _save_session_state(session_id, sim)
                # Also save to snapshots table
                db = await get_db()
                try:
                    await db.execute(
                        """INSERT INTO session_snapshots (session_id, step_number, grid_state, metrics_json)
                           VALUES (?, ?, ?, ?)""",
                        (session_id, sim.step_num, sim.board.data.tobytes(), json.dumps(sim._collect_metrics())),
                    )
                    await db.commit()
                finally:
                    await db.close()
                await websocket.send_json({"type": "snapshot_saved", "step": sim.step_num})

    except WebSocketDisconnect:
        running = False
        if task:
            task.cancel()
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        running = False
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        await _save_session_state(session_id, sim)
