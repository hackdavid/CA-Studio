# Development Log

Chronological record of major CA Lab milestones. For file-level detail see [memory.md](../../memory.md).

## Phase 1 — Engine migration

- Ported legacy Java CA laboratory to Python (`ca_engine`)
- Implemented `Grid`, `Board`, `Simulator`, rule compiler
- YAML rule format + legacy `.txt` loader
- Built-in metrics: density, entropy
- CLI (`ca-lab`) for headless experiments
- Parity tests against reference Java rules

## Phase 2 — Web platform consolidation

- Merged fragmented `web/`, `web_ui/`, `frontend/` into single `app.py`
- Clean URLs without `.html` extensions
- FastAPI routers: rules, sessions, simulations (WebSocket)
- SQLite persistence with session snapshots
- Professional UI: landing, dashboard, simulation pages
- Design system (`design-system/ca-lab/MASTER.md`)

## Phase 3 — UX and canvas

- 10% / 80% / 10% simulation layout (controls · canvas · metrics)
- Dynamic canvas sizing with device pixel ratio
- Real-time WebSocket frames (JSON metadata + binary grid)
- Drawing tools with brush picker
- Grid line toggle, speed control, PNG export

## Phase 4 — Experiment configuration (current)

- **New Session modal enhancements:**
  - Editable **Number of States (K)** auto-filled from rule YAML
  - Searchable **metrics** multi-select via `/api/metrics/`
  - Seed types: random, center, empty
- **Simulation drawing:**
  - Color swatch grid for K states
  - Incremental cell painting (low latency)
  - **Start** sends drawn grid as initial state
- **Backend:**
  - Seed applied on session create → `current_grid` stored
  - Metrics API router
  - Read-only numpy grid fix (`Grid.data` setter copies buffer)
  - Paint errors isolated from WebSocket loop

## Known fixes

| Issue | Resolution |
|-------|------------|
| `is_builtin` column missing | `fix_database.py` migration |
| Read-only grid on paint | Copy `frombuffer` arrays in `Grid.data` setter |
| WebSocket crash on paint | Per-action error handling in simulations router |
| Unicode console on Windows | Text markers in `start.py` |

## Open items

- [ ] Rule editor UI (dashboard placeholder)
- [ ] Custom metric editor UI
- [ ] Add `aiosqlite` to `requirements.txt`
- [ ] Capture screenshots into `documents/assets/`
- [ ] CSV/JSON export from web UI
- [ ] LICENSE file at repository root

## Version

Application version: **1.0.0** (`app.py`, `/health`)
