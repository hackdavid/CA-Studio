# Features

CA Lab is a full-stack framework for designing, running, and analyzing cellular automata experiments.

## Core capabilities

### Multi-state cellular automata

- Support for **K states** (2–101), configured per session
- State count auto-populated from rule YAML (`states:` field)
- User-editable before experiment creation
- Color swatch brush picker on the simulation page

### Rule system

- **28+ built-in rules** in `rules/*.yaml` (Conway, 413, expansion, dormancy, etc.)
- YAML schema with transitions: `from`, `neighbors`, `to`
- Legacy `.txt` rule import via `LegacyRuleLoader`
- Rule validation API
- Custom rules via `POST /api/rules`

Example rule header:

```yaml
name: Conway
version: '1.0'
states: 2
neighbourhood: moore8
transitions:
  - from: [0]
    neighbors: [3]
    to: 1
```

### Neighbourhoods

- Moore 8 (default)
- Moore 9, Von Neumann 4/5
- Toroidal wrapping on all edges

### Session management

- Named experiments with full provenance
- SQLite persistence (`ca_lab.db`)
- Board dimensions, rule, seed config, metrics, current grid, step count
- Snapshots at any step
- Delete and resume sessions from dashboard

### Initial conditions (seeds)

| Seed type | Behavior |
|-----------|----------|
| Random (30% / 50%) | Fills non-zero states at given density |
| Center | Single live cell at grid center |
| Empty | All zeros — paint manually |
| Custom grid | Draw on canvas; sent on **Start** |

### Real-time simulation

- WebSocket stream at `/api/sim/ws/{session_id}`
- Start / pause / step / reset / speed controls
- Sub-100 ms frame delivery on typical boards
- Incremental canvas painting (no full redraw per stroke)

### Metrics

Built-in registry metrics:

| Metric | Description |
|--------|-------------|
| `density` | Fraction of non-zero cells |
| `entropy` | Shannon entropy over all states |
| `entropy_nonzero` | Entropy excluding state 0 |

- Searchable multi-select in New Session modal
- Live display on simulation right panel
- Per-step collection in simulation loop

### Interactive canvas

- Paint cells with selected state color
- Drawing disabled while simulation is running (pause first)
- Grid line toggle
- PNG export
- Responsive cell sizing (board fills viewport)

### CLI and headless mode

```bash
ca-lab play --rule Conway --width 64 --height 64 --states 3
ca-lab run -f configs/experiment.yaml --headless
ca-lab list-rules
ca-lab list-metrics
ca-lab validate --rule Conway --steps 100
```

### Renderers

- **Web** — primary UI (`web/static/`)
- **Pygame** — desktop visualization (`ca_engine/renderers/`)
- **Headless** — batch experiments and data export

## Design principles

- **Reproducibility** — sessions store rule, seed, grid, and step history
- **Separation of concerns** — `ca_engine` is UI-agnostic
- **Open extension** — plugin registry for metrics; YAML for rules
- **Academic UX** — accessible typography, reduced motion, clear hierarchy

## Roadmap (planned)

- Custom rule editor in dashboard UI
- Custom metric formula editor
- CSV/JSON experiment export from web UI
- Jupyter notebook integration
- Multi-user authentication
