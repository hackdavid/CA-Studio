# CA Studio — Repository Memory

> Living document: project map, file locations, features, and development history.  
> Location: `documents/reference/memory.md`  
> Repository: https://github.com/hackdavid/CA-Studio  
> Last updated: June 2026 · Version 1.0.0

---

## What is this project?

**CA Studio** (Cellular Automata Studio) is an open-source research and education framework for exploring multi-state cellular automata. It replaces a legacy Java desktop lab with:

- A **NumPy simulation engine** (`ca_engine`)
- A **FastAPI web application** with real-time WebSocket simulation
- A **CLI** for batch and headless experiments
- **28+ YAML rules** migrated from academic reference code

**Institution context:** Developed for Roehampton University teaching and research.

---

## Quick reference

| Item | Value |
|------|-------|
| Entry point (web) | `python start.py` → http://127.0.0.1:8000 |
| Main app | `app.py` |
| Database | `ca_lab.db` (SQLite, auto-created) |
| Rules | `rules/*.yaml` |
| Docs hub | `documents/README.md` |
| Design system | `design-system/ca-lab/MASTER.md` |

---

## Directory map

```
ca_project/
│
├── app.py                      # FastAPI application (pages + API mount)
├── start.py                    # Server launcher
├── memory.md                   # THIS FILE — repo memory (documents/reference/)
├── README.md                   # Open-source homepage
├── requirements.txt            # Python dependencies
├── fix_database.py             # SQLite schema migration helper
├── test_consolidated_app.py    # App integration tests
│
├── documents/                  # Organized documentation
│   ├── README.md               # Doc index
│   ├── reference/              # Archived root notes + memory.md
│   ├── getting-started/        # Install + quick start
│   ├── user-guide/             # Navigation, features, experiments
│   ├── developer/              # Architecture, API, engine, dev log
│   └── assets/                 # Screenshot placeholders
│
├── docs/                       # Research drafts (older)
│   ├── README.md
│   ├── WHITEPAPER_DRAFT.md
│   └── WORKFLOW_OBSERVATIONS.md
│
├── web/                        # Web API + frontend
│   ├── database.py             # SQLite schema, seed rules/metrics
│   ├── models.py               # Pydantic models
│   ├── routers/
│   │   ├── rules.py            # GET/POST /api/rules
│   │   ├── sessions.py         # GET/POST /api/sessions, grid, snapshots
│   │   ├── metrics.py          # GET /api/metrics
│   │   └── simulations.py      # WS /api/sim/ws/{session_id}
│   └── static/
│       ├── landing.html        # Home page
│       ├── dashboard.html      # Session/rule/metric management
│       ├── sim.html            # Real-time simulation + canvas
│       ├── js/app.js           # API client, SimulationClient, toast
│       └── legacy/             # Archived older UI pages
│
├── ca_engine/                  # Simulation engine (framework core)
│   ├── core/
│   │   ├── grid.py             # Toroidal grid; writable copy on assign
│   │   ├── board.py            # Board with bbox tracking
│   │   ├── simulator.py        # Step loop, metrics attachment
│   │   ├── seed.py             # single, random, pattern seeds
│   │   ├── neighbourhood.py    # moore8, moore9, n4, n5
│   │   └── palette.py          # State colors
│   ├── rules/
│   │   ├── yaml_loader.py      # YAML → RuleTable
│   │   ├── legacy_loader.py    # .txt rules
│   │   ├── compiler.py         # Rule compilation
│   │   └── validator.py        # Validation
│   ├── metrics/
│   │   ├── registry.py         # density, entropy, entropy_nonzero
│   │   ├── density.py
│   │   └── entropy.py
│   ├── config/experiment.py    # ExperimentConfig for CLI YAML
│   ├── renderers/pygame_renderer.py
│   └── logging/                # Metrics logger, provenance
│
├── cli/main.py                 # ca-lab CLI (Typer)
├── rules/                      # 28 built-in YAML rules
├── tests/                      # pytest (simulator, parity)
├── scripts/                    # cleanup_db, pygame screenshot
├── design-system/ca-lab/       # UI/UX master doc
├── reference_code/             # Original Java reference
└── configs/                    # Example experiment YAMLs (if present)
```

---

## Web pages and routes

| URL | File | Purpose |
|-----|------|---------|
| `/` | `web/static/landing.html` | Marketing + Conway preview |
| `/dashboard` | `web/static/dashboard.html` | Create/manage sessions |
| `/simulation/{id}` | `web/static/sim.html` | Live CA + drawing |
| `/api/docs` | Swagger | REST API |
| `/api/sim/ws/{id}` | `simulations.py` | WebSocket simulation |

---

## API endpoints summary

### Rules — `web/routers/rules.py`
- `GET/POST /api/rules/`
- `GET/PUT/DELETE /api/rules/{id}`
- `POST /api/rules/{id}/validate`

### Sessions — `web/routers/sessions.py`
- `GET/POST /api/sessions/`
- `GET/PUT/DELETE /api/sessions/{id}`
- `GET /api/sessions/{id}/grid`
- Snapshots: list, get, post

**Session create flow:** inserts row → `_build_initial_grid()` applies seed → stores `current_grid` BLOB.

### Metrics — `web/routers/metrics.py`
- `GET /api/metrics/` — registry + DB custom metrics

### Simulation WS — `web/routers/simulations.py`
Actions: `start` (with optional `grid`), `pause`, `stop`, `step`, `reset`, `paint`, `speed`, `snapshot`

---

## Key frontend behaviors

### Dashboard (`dashboard.html`)
- `allRules`, `allSessions`, `allMetrics` loaded on page load
- New Session modal:
  - Rule search + select → updates `num-states-input` from YAML `states:`
  - Metrics search + multi-checkbox from `/api/metrics/`
  - Seed map: random_30, random_50, center, empty
- `createSession()` → POST `/api/sessions/` → redirect `/simulation/{id}`

### Simulation (`sim.html`)
- Loads session + grid via REST
- WebSocket `SimulationClient` from `app.js`
- Color **swatch grid** for states 0…K−1
- **Incremental `drawCell()`** for painting (no full canvas redraw)
- **`startSim()`** sends `currentGrid` on start
- `cloneGrid()` ensures mutable local copy

### Shared JS (`web/static/js/app.js`)
- `api.get/post/put/delete`
- `SimulationClient` class
- `toast()` notifications

---

## Database schema

**rules** — name, yaml_content, is_builtin, is_editable, description, category

**sessions** — name, rule_id, board_width/height, neighbourhood, num_states, seed_config (JSON), current_grid (BLOB), current_step, status, metrics_enabled (JSON)

**session_snapshots** — session_id, step_number, grid_state, metrics_json

**custom_metrics** — name, formula, description, is_builtin

Seeded on startup in `app.py` lifespan: `init_db()`, `seed_builtin_rules()`, `seed_builtin_metrics()`.

---

## Built-in rules (sample)

| File | States | Notes |
|------|--------|-------|
| Conway.yaml | 2 | Game of Life |
| 413.yaml | varies | Legacy rule |
| expansion.yaml | 101 | Large state space |
| DormancyA/B/C.yaml | 5–101 | Dormancy experiments |
| TGA.yaml | 5 | Test rule |

Full list: `rules/*.yaml` (28 files).

---

## Built-in metrics

| Name | Module | Description |
|------|--------|-------------|
| density | `metrics/density.py` | Non-zero cell fraction |
| entropy | `metrics/entropy.py` | Shannon H over states |
| entropy_nonzero | registry lambda | H excluding state 0 |

---

## What we have done (timeline)

### Consolidation
- Single `app.py` replaced multiple web entry points
- Clean URLs, legacy pages under `web/static/legacy/`
- Fixed DB schema (`is_builtin`, etc.) via `fix_database.py`
- Windows console encoding fixes in `start.py`

### UI/UX
- Landing, dashboard, simulation professional redesign
- Tailwind + Crimson Pro / Atkinson Hyperlegible fonts
- Responsive simulation layout with full-width canvas

### Experiment features (recent)
- Editable **K states** in New Session modal (from rule YAML)
- Searchable **metrics** multi-select
- **Empty seed** + canvas drawing as initial state
- **Start** passes drawn grid to server
- `/api/metrics/` endpoint
- Seed initialization on session create

### Bug fixes (recent)
- **Read-only grid:** `np.frombuffer` grids copied in `Grid.data` setter
- Paint no longer kills WebSocket connection
- Server skips full frame on paint for performance

---

## CLI commands

```bash
ca-lab run -f configs/experiment.yaml
ca-lab play --rule Conway --width 64 --height 64 --states 3
ca-lab list-rules
ca-lab list-metrics
ca-lab validate --rule Conway --steps 100
```

---

## Tests

```bash
pytest tests/ -q
python test_consolidated_app.py
```

Key files: `tests/test_simulator.py`, `tests/test_parity.py`

---

## Legacy / archived root markdown

| File | Status |
|------|--------|
| QUICK_START.md | Superseded by `documents/getting-started/` |
| CLEANUP_GUIDE.md | Project cleanup notes |
| CONSOLIDATION_SUMMARY.md | Consolidation report |
| FINAL_STATUS.md | Status report |
| CANVAS_*.md, UX_*, LAYOUT_* | Design iteration notes |
| REFERENCE_CODE_ANALYSIS.md | Java reference analysis |

---

## Dependencies (notable)

From `requirements.txt`: numpy, fastapi, uvicorn, pydantic, pyyaml, pygame, pytest, etc.

**Also required for web:** `aiosqlite` (install separately until added to requirements).

---

## How to extend

1. **New rule:** add `rules/MyRule.yaml`, restart server (auto-seeds new files)
2. **New metric:** implement `Metric` subclass, register in `MetricRegistry`
3. **New API route:** add router in `web/routers/`, include in `app.py`
4. **UI change:** edit `web/static/*.html` or `js/app.js`

---

## Contacts and license

- Academic project — Roehampton University
- Intended license: MIT (add `LICENSE` file when publishing)
- Full user docs: [documents/README.md](documents/README.md)

---

*Update this file when adding major features, routes, or structural changes.*
