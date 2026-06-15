# CA Engine

The `ca_engine` package is the computational core of CA Lab. It has no web dependencies and can be used from CLI scripts, notebooks, or tests.

## Package layout

```
ca_engine/
├── core/
│   ├── grid.py          # Toroidal uint8 array
│   ├── board.py         # Grid + bounding box
│   ├── simulator.py     # Main step loop
│   ├── seed.py          # Initial conditions
│   ├── neighbourhood.py # Neighbor counting
│   └── palette.py       # Color maps
├── rules/
│   ├── yaml_loader.py   # YAML → RuleTable
│   ├── legacy_loader.py # .txt legacy rules
│   ├── compiler.py      # Rule table compilation
│   ├── validator.py     # Rule validation
│   └── rule_row.py      # Row format
├── metrics/
│   ├── registry.py      # Plugin registry
│   ├── density.py
│   └── entropy.py
├── config/
│   └── experiment.py    # ExperimentConfig schema
├── renderers/
│   └── pygame_renderer.py
└── logging/
    ├── metrics_logger.py
    └── provenance.py
```

## Simulation step

```python
from ca_engine.core.board import Board
from ca_engine.core.simulator import Simulator
from ca_engine.core.neighbourhood import Neighbourhood
from ca_engine.core.seed import SeedConfig
from ca_engine.rules.yaml_loader import YAMLRuleLoader

loader = YAMLRuleLoader()
table = loader.load("Conway")

board = Board(64, 64)
sim = Simulator(board, table, Neighbourhood.from_name("moore8"))
sim.reset(SeedConfig(type="single", state=1, position="center"))

for _ in range(100):
    sim.step()

print(sim.step_num, sim._collect_metrics())
```

## Rule YAML schema

```yaml
name: MyRule
version: "1.0"
states: 5
neighbourhood: moore8
description: Optional human text
transitions:
  - from: [1]
    neighbors: [2, 3]
    to: 1
  - from: [0]
    neighbors: [3]
    to: 1
```

- `from` — current state(s) as int or list
- `neighbors` — neighbor count(s) that trigger the transition
- `to` — next state (int) or `"same"`

## Seed configuration

```python
SeedConfig(type="single", state=1, position="center")
SeedConfig(type="random", density=0.3, states=[1, 2, 3])
SeedConfig(type="pattern", pattern=[[0,1],[1,0]])
```

## Adding a metric

```python
from ca_engine.metrics.registry import MetricRegistry
from ca_engine.metrics.base import Metric

class MyMetric(Metric):
    def on_init(self, shape, num_states): ...
    def on_step(self, grid, step): ...
    def value(self): ...

registry = MetricRegistry()
registry.register("my_metric", MyMetric, "custom", "My description")
```

## Experiment YAML (CLI)

```yaml
rule: Conway
width: 64
height: 64
num_states: 2
neighbourhood: moore8
steps: 1000
global_seed: 42
metrics:
  - density
  - entropy
seed:
  type: random
  density: 0.3
  states: [1]
log:
  metrics_every: 10
```

Run: `ca-lab run -f experiment.yaml`

## Tests

```bash
pytest tests/test_simulator.py tests/test_parity.py -v
```

Parity tests compare Python engine output against legacy Java reference behavior.

## Performance notes

- NumPy vectorized neighbor counting
- Double-buffered grid updates per step
- Board sizes up to 512×512 supported in web UI (hardware dependent)
