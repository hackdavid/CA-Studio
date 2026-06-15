<p align="center">
  <strong>CA Studio</strong><br>
  <sub>Cellular Automata Laboratory — research platform for multi-state CA experimentation</sub>
</p>

<p align="center">
  <a href="https://github.com/hackdavid/CA-Studio"><img src="https://img.shields.io/badge/GitHub-CA--Studio-181717?logo=github" alt="GitHub"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white" alt="FastAPI"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT"></a>
</p>

---

## Overview

**CA Studio** is an open-source laboratory framework for designing, executing, and analyzing **multi-state cellular automata**. It provides a reproducible pipeline from rule definition through session management, real-time simulation, and quantitative metrics — suitable for coursework, thesis work, and computational research.

The platform replaces a legacy Java desktop laboratory with a modular Python stack:

- **`ca_engine`** — NumPy-based simulation core (grid, rules, neighbourhoods, metrics)
- **Web application** — FastAPI REST API, WebSocket simulation, session persistence
- **CLI** — Headless and batch experiment execution via `ca-lab`

Repository: **[github.com/hackdavid/CA-Studio](https://github.com/hackdavid/CA-Studio)**

---

## Capabilities

### Simulation engine

| Capability | Detail |
|------------|--------|
| State space | 2–101 states per experiment (K configurable per session) |
| Neighbourhoods | Moore 8/9, Von Neumann 4/5, toroidal boundaries |
| Rule format | Human-readable YAML with transition tables |
| Rule library | 28+ built-in rules (Conway, 413, expansion, dormancy, …) |
| Legacy import | Original `.txt` rule tables via `LegacyRuleLoader` |
| Validation | Rule table validation before execution |

### Web laboratory

| Capability | Detail |
|------------|--------|
| Sessions | Named experiments with persisted grid, step count, and configuration |
| Initial conditions | Random density, center seed, empty grid, or hand-drawn patterns |
| Canvas | Interactive painting; drawn state submitted as initial condition on run |
| Real-time control | Start, pause, single-step, reset, variable speed (10–500 ms) |
| Metrics | Density, Shannon entropy, entropy (non-zero); selectable per session |
| Export | PNG snapshot of current board state |
| API | Open REST + WebSocket interfaces for integration |

### Reproducibility

- SQLite storage of rule ID, board dimensions, seed configuration, metrics, and grid snapshots  
- Session provenance suitable for lab reports and research notes  
- CLI `ExperimentConfig` YAML for scripted, headless runs  

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Presentation   landing · dashboard · simulation (HTML/JS)   │
├──────────────────────────────────────────────────────────────┤
│  API Layer      FastAPI — rules · sessions · metrics · WS    │
├──────────────────────────────────────────────────────────────┤
│  Engine         ca_engine — Simulator · RuleTable · Metrics  │
├──────────────────────────────────────────────────────────────┤
│  Data           SQLite (ca_lab.db)  ·  rules/*.yaml          │
└──────────────────────────────────────────────────────────────┘
```

**Repository layout**

```
CA-Studio/
├── app.py                 # FastAPI entry point
├── start.py               # Development server launcher
├── ca_engine/             # Simulation framework (importable package)
├── web/                   # Routers, models, static UI
├── rules/                 # YAML rule definitions
├── cli/                   # Typer CLI (ca-lab)
├── documents/             # Documentation
├── tests/                 # pytest suite
└── README.md
```

Full design notes: [documents/developer/architecture.md](documents/developer/architecture.md)

---

## Installation

**Requirements:** Python 3.10+, modern browser (Chrome, Firefox, Edge)

```bash
git clone https://github.com/hackdavid/CA-Studio.git
cd CA-Studio

python -m venv env
# Windows
.\env\Scripts\activate
# macOS / Linux
# source env/bin/activate

pip install -r requirements.txt
pip install aiosqlite
```

Start the server:

```bash
python start.py
```

| Resource | URL |
|----------|-----|
| Application | http://127.0.0.1:8000/ |
| Dashboard | http://127.0.0.1:8000/dashboard |
| API (Swagger) | http://127.0.0.1:8000/api/docs |
| Health check | http://127.0.0.1:8000/health |

The database is created automatically on first launch. Built-in rules and metrics are seeded from `rules/` and the metrics registry.

Detailed setup: [documents/getting-started/installation.md](documents/getting-started/installation.md)

---

## Usage

### Web workflow

1. Open the **dashboard** and click **New Session**.
2. Select a rule (state count K is read from the rule YAML; editable).
3. Set board size, seed type, and metrics.
4. On the **simulation** page, paint an initial pattern if desired.
5. Click **Start** — the current grid is sent as the initial state.
6. Monitor metrics in the side panel; save snapshots or export PNG.

Step-by-step guide: [documents/getting-started/quick-start.md](documents/getting-started/quick-start.md)

### API example

```bash
curl -X POST http://127.0.0.1:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Conway 64",
    "rule_id": 1,
    "board_width": 64,
    "board_height": 64,
    "num_states": 2,
    "seed_config": {"type": "empty"},
    "metrics_enabled": ["density", "entropy"]
  }'
```

Then open `http://127.0.0.1:8000/simulation/{id}`.

API reference: [documents/developer/api-reference.md](documents/developer/api-reference.md)

### CLI

```bash
ca-lab list-rules
ca-lab list-metrics
ca-lab play --rule Conway --width 64 --height 64
ca-lab run -f configs/experiment.yaml --headless
```

Engine documentation: [documents/developer/ca-engine.md](documents/developer/ca-engine.md)

---

## Rule format (YAML)

```yaml
name: Conway
version: "1.0"
states: 2
neighbourhood: moore8
transitions:
  - from: [0]
    neighbors: [3]
    to: 1
  - from: [1]
    neighbors: [2, 3]
    to: 1
```

Add new rules under `rules/`; they are registered on server startup.

---

## Documentation

| Document | Audience |
|----------|----------|
| [Documentation index](documents/README.md) | All guides |
| [Installation](documents/getting-started/installation.md) | Setup |
| [Quick start](documents/getting-started/quick-start.md) | First experiment |
| [UI navigation](documents/user-guide/navigation.md) | Interface tour |
| [Features](documents/user-guide/features.md) | Capability reference |
| [Experiments](documents/user-guide/experiments.md) | Research workflow |
| [Architecture](documents/developer/architecture.md) | System design |
| [API reference](documents/developer/api-reference.md) | REST + WebSocket |
| [Repository memory](documents/reference/memory.md) | File map & history |
| [Dev log](documents/developer/dev_log.md) | Milestones |

Research drafts: [docs/WHITEPAPER_DRAFT.md](docs/WHITEPAPER_DRAFT.md)

---

## Development

```bash
pytest tests/ -q
python test_consolidated_app.py
```

### Excluded from version control

The following are intentionally **not** pushed to GitHub (see `.gitignore`):

- `.cursor/`, `.claude/` — local AI/editor configuration  
- `reference_code/` — legacy Java reference (keep locally for parity work)  
- `env/`, `ca_lab.db` — virtualenv and local database  

---

## Technology stack

| Layer | Components |
|-------|------------|
| Runtime | Python 3.10+, NumPy, Pydantic v2 |
| API | FastAPI, Uvicorn, aiosqlite |
| Real-time | WebSockets (binary grid frames) |
| Frontend | HTML5, Tailwind CSS, vanilla JavaScript |
| Persistence | SQLite |
| CLI | Typer |
| Quality | pytest, ruff, mypy (see `pyproject.toml`) |

---

## Troubleshooting

| Issue | Action |
|-------|--------|
| Port 8000 in use | Stop the existing process or change the port in `start.py` |
| Database schema error | Run `python fix_database.py` |
| Reset all sessions | Delete `ca_lab.db` and restart the server |

---

## Contributing

Contributions are welcome via pull request on [CA-Studio](https://github.com/hackdavid/CA-Studio).

1. Fork the repository  
2. Create a feature branch  
3. Run `pytest tests/`  
4. Open a PR with a clear description of the change  

---

## Acknowledgments

Developed in an academic context for teaching and research in complex systems and cellular automata. The engine design prioritizes parity with a prior Java reference implementation and extensibility for custom rules and metrics.

---

## License

MIT License — see [LICENSE](LICENSE) (to be added for release).

---

<p align="center">
  <strong>CA Studio</strong> — reproducible multi-state cellular automata for the lab and the classroom.
</p>
