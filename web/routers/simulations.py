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
from ca_engine.core.seed import SeedConfig
from ca_engine.metrics.dynamic import DynamicMetricFactory
from ca_engine.metrics.registry import MetricRegistry
from ca_engine.rules.yaml_loader import YAMLRuleLoader
from ca_engine.rules.legacy_loader import LegacyRuleLoader
from ca_engine.evolution.chromosome import Chromosome
from ca_engine.evolution.fitness import FitnessEvaluator
from ca_engine.evolution.pipeline import EvolutionPipeline
from ca_engine.evolution.breed_pipeline import BreedPipeline
from web.routers.sessions import _build_initial_grid
from web.services.metric_loader import fetch_all_custom_metrics

router = APIRouter(prefix="/api/sim", tags=["simulations"])


async def _log_event(session_id: int, step: int, action_type: str, payload: dict[str, Any]) -> None:
    """Log a session event for deterministic replay."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO session_events (session_id, step_number, action_type, payload) VALUES (?, ?, ?, ?)",
            (session_id, step, action_type, json.dumps(payload)),
        )
        await db.commit()
    finally:
        await db.close()

# Active simulation tasks
active_simulations: dict[int, asyncio.Task] = {}
# Active evolution pipelines
active_evolutions: dict[int, EvolutionPipeline] = {}
# Active breed pipelines
active_breeds: dict[int, BreedPipeline] = {}


async def _handle_evolution_websocket(websocket: WebSocket, session_id: int) -> None:
    """Handle WebSocket for evolution mode."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT s.board_width, s.board_height, s.neighbourhood, s.num_states,
                      s.seed_config, r.yaml_content, r.name as rule_name, s.current_grid,
                      e.target_image, e.fitness_weights_json, e.population_size,
                      e.generations, e.mutation_rate, e.evolve_rule, e.evolve_seed,
                      e.constraints_json
               FROM sessions s
               JOIN rules r ON s.rule_id = r.id
               LEFT JOIN evolution_configs e ON e.session_id = s.id
               WHERE s.id = ?""",
            (session_id,),
        )
        row = await cursor.fetchone()
        if not row:
            await websocket.send_json({"type": "error", "message": "Session not found"})
            await websocket.close()
            return
    finally:
        await db.close()

    # Parse config
    width = row["board_width"]
    height = row["board_height"]
    num_states = row["num_states"]
    neighbourhood = row["neighbourhood"]
    weights = json.loads(row["fitness_weights_json"] or '{"similarity": 0.5, "metrics": 0.3, "simplicity": 0.2}')
    population_size = row["population_size"] or 30
    generations = row["generations"] or 100
    mutation_rate = row["mutation_rate"] or 0.05

    # Build target grid from target image if available
    target_grid = None
    if row["target_image"]:
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(row["target_image"])).convert("RGB")
            # Resize to match board and quantize to states
            img = img.resize((width, height), Image.Resampling.NEAREST)
            arr = np.array(img)
            # Convert RGB to states using simple quantization
            gray = np.mean(arr, axis=2)
            target_grid = (gray / 255.0 * (num_states - 1)).astype(np.uint8)
        except Exception:
            pass

    # Build fitness evaluator
    evaluator = FitnessEvaluator(
        target_grid=target_grid,
        weights=weights,
        steps=20,
        width=width,
        height=height,
    )

    # Seed rule
    seed_rule = None
    if row["yaml_content"]:
        try:
            seed_rule = Chromosome.from_rule_yaml(row["yaml_content"], num_states, neighbourhood)
        except Exception:
            pass

    pipeline = EvolutionPipeline(
        population_size=population_size,
        generations=generations,
        mutation_rate=mutation_rate,
        fitness_evaluator=evaluator,
        seed_rule=seed_rule,
    )
    active_evolutions[session_id] = pipeline

    task: asyncio.Task | None = None

    async def evolution_loop() -> None:
        """Run evolution and stream best candidate each generation."""
        for result in pipeline.run():
            if result.get("type") == "paused":
                await asyncio.sleep(0.5)
                continue
            if result.get("type") == "done":
                await websocket.send_json({
                    "type": "evolution_done",
                    "generation": result["generation"],
                    "best_fitness": result["best_fitness_ever"],
                })
                break

            best = result["best_chromosome"]
            sim = best.to_simulator(width, height)
            # Run a few steps to show evolved behavior
            for _ in range(5):
                sim.step()

            palette = Palette.default(num_states)
            await websocket.send_json({
                "type": "evolution",
                "generation": result["generation"],
                "best_fitness": result["best_fitness"],
                "best_fitness_ever": result["best_fitness_ever"],
                "mean_fitness": result.get("mean_fitness", 0),
                "grid_shape": sim.board.data.shape,
                "palette": palette.colors.tolist(),
            })
            await websocket.send_bytes(sim.board.data.tobytes())

            # Update DB with current generation and best fitness
            db2 = await get_db()
            try:
                await db2.execute(
                    "UPDATE evolution_configs SET current_generation = ?, best_fitness = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                    (result["generation"], result["best_fitness"], session_id),
                )
                await db2.commit()
            finally:
                await db2.close()

            # Yield control
            await asyncio.sleep(0.1)

    try:
        while True:
            msg = await websocket.receive_json()
            action = msg.get("action")

            if action == "start_evolution":
                if not task or task.done():
                    task = asyncio.create_task(evolution_loop())
                await websocket.send_json({"type": "status", "status": "evolving"})

            elif action == "pause":
                pipeline.pause()
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                await websocket.send_json({"type": "status", "status": "paused"})

            elif action == "stop":
                pipeline.stop()
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                await websocket.send_json({"type": "status", "status": "stopped"})

            elif action == "snapshot":
                db2 = await get_db()
                try:
                    await db2.execute(
                        """INSERT INTO session_snapshots (session_id, step_number, grid_state, metrics_json)
                           VALUES (?, ?, ?, ?)""",
                        (session_id, pipeline.current_generation, b"", json.dumps({"best_fitness": pipeline.best_fitness_ever})),
                    )
                    await db2.commit()
                finally:
                    await db2.close()
                await websocket.send_json({"type": "snapshot_saved", "step": pipeline.current_generation})

    except WebSocketDisconnect:
        pipeline.stop()
        if task:
            task.cancel()
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        pipeline.stop()
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        if session_id in active_evolutions:
            del active_evolutions[session_id]


async def _handle_breed_websocket(websocket: WebSocket, session_id: int) -> None:
    """Handle WebSocket for breed mode."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT s.board_width, s.board_height, s.neighbourhood, s.num_states,
                      s.seed_config, r.yaml_content, r.name as rule_name, s.current_grid
               FROM sessions s
               JOIN rules r ON s.rule_id = r.id
               WHERE s.id = ?""",
            (session_id,),
        )
        row = await cursor.fetchone()
        if not row:
            await websocket.send_json({"type": "error", "message": "Session not found"})
            await websocket.close()
            return
    finally:
        await db.close()

    width = row["board_width"]
    height = row["board_height"]
    num_states = row["num_states"]
    neighbourhood = row["neighbourhood"]

    seed_rule = None
    if row["yaml_content"]:
        try:
            seed_rule = Chromosome.from_rule_yaml(row["yaml_content"], num_states, neighbourhood)
        except Exception:
            pass

    pipeline = BreedPipeline(
        population_size=9,
        num_states=num_states,
        neighbourhood=neighbourhood,
        mutation_rate=0.1,
        seed_rule=seed_rule,
    )
    active_breeds[session_id] = pipeline

    async def send_population() -> None:
        """Send current population grids."""
        grids = pipeline.get_grids(width, height, steps=5)
        palette = Palette.default(num_states)
        await websocket.send_json({
            "type": "population",
            "generation": pipeline.generation,
            "grid_shape": [height, width],
            "palette": palette.colors.tolist(),
            "count": len(grids),
        })
        for grid in grids:
            await websocket.send_bytes(grid.tobytes())

    # Send initial population
    await send_population()

    try:
        while True:
            msg = await websocket.receive_json()
            action = msg.get("action")

            if action == "breed_next_generation":
                parents = msg.get("parents", [])
                pipeline.breed_next_generation(parents)
                await send_population()
                await websocket.send_json({"type": "status", "status": "bred", "generation": pipeline.generation})

            elif action == "reset_population":
                pipeline.reset()
                await send_population()
                await websocket.send_json({"type": "status", "status": "reset", "generation": pipeline.generation})

            elif action == "snapshot":
                db2 = await get_db()
                try:
                    await db2.execute(
                        """INSERT INTO session_snapshots (session_id, step_number, grid_state, metrics_json)
                           VALUES (?, ?, ?, ?)""",
                        (session_id, pipeline.generation, b"", json.dumps({"generation": pipeline.generation})),
                    )
                    await db2.commit()
                finally:
                    await db2.close()
                await websocket.send_json({"type": "snapshot_saved", "step": pipeline.generation})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        if session_id in active_breeds:
            del active_breeds[session_id]


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
        sim.session_seed_config = json.loads(row["seed_config"] or "{}")

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

    # Load session metadata first to determine mode
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT mode FROM sessions WHERE id = ?", (session_id,)
        )
        row = await cursor.fetchone()
        session_mode = row["mode"] if row else "simulate"
    finally:
        await db.close()

    if session_mode == "evolve":
        await _handle_evolution_websocket(websocket, session_id)
        return
    if session_mode == "breed":
        await _handle_breed_websocket(websocket, session_id)
        return

    try:
        sim = await _load_simulator(session_id)
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
        return

    running = False
    fps = 10
    task: asyncio.Task | None = None

    # Capture original grid for image fidelity
    original_grid = sim.board.data.copy()
    seed_config = sim.session_seed_config if hasattr(sim, 'session_seed_config') else {}
    image_palette = seed_config.get('palette') if isinstance(seed_config, dict) else None

    async def send_frame() -> None:
        """Send current state to client."""
        grid = sim.board.data
        metrics = sim._collect_metrics()

        # Compute image fidelity if an image seed was used
        if image_palette is not None:
            mse = float(np.mean((grid.astype(np.float32) - original_grid.astype(np.float32)) ** 2))
            metrics["image_fidelity"] = round(mse, 4)

        # Use image seed palette if available, else default
        palette_colors = image_palette if image_palette else Palette.default(sim.board.data.max() + 1).colors.tolist()

        await websocket.send_json({
            "type": "frame",
            "step": sim.step_num,
            "metrics": metrics,
            "grid_shape": grid.shape,
            "palette": palette_colors,
        })
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
                seed_cfg = sim.session_seed_config if hasattr(sim, 'session_seed_config') else {}
                if seed_cfg and seed_cfg.get("type"):
                    sim.reset(SeedConfig.model_validate(seed_cfg))
                else:
                    sim.reset()
                await _save_session_state(session_id, sim)
                await _log_event(session_id, sim.step_num, "reset", seed_cfg if isinstance(seed_cfg, dict) else {})
                await send_frame()
                await websocket.send_json({"type": "status", "status": "stopped", "step": 0})

            elif action == "paint":
                x = msg.get("x", 0)
                y = msg.get("y", 0)
                state = msg.get("state", 1)
                try:
                    sim.board.set(x, y, state)
                    await _save_session_state(session_id, sim)
                    await _log_event(session_id, sim.step_num, "paint", {"x": x, "y": y, "state": state})
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
