# API Reference

Base URL: `http://127.0.0.1:8000`

Interactive docs: [Swagger UI](http://127.0.0.1:8000/api/docs) · [ReDoc](http://127.0.0.1:8000/api/redoc)

## Health and info

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health |
| GET | `/api/info` | Endpoint map |

## Rules

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/rules/` | List all rules |
| GET | `/api/rules/{id}` | Get rule by ID |
| POST | `/api/rules/` | Create custom rule |
| PUT | `/api/rules/{id}` | Update rule (non-built-in) |
| DELETE | `/api/rules/{id}` | Delete rule |
| POST | `/api/rules/{id}/validate` | Validate rule table |

### Rule object

```json
{
  "id": 1,
  "name": "Conway",
  "yaml_content": "...",
  "is_builtin": true,
  "is_editable": false,
  "description": "Conway's Game of Life",
  "category": "experimental",
  "created_at": "2026-01-01 12:00:00"
}
```

## Sessions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sessions/` | List sessions |
| GET | `/api/sessions/{id}` | Get session |
| POST | `/api/sessions/` | Create session |
| PUT | `/api/sessions/{id}` | Update session |
| DELETE | `/api/sessions/{id}` | Delete session |
| GET | `/api/sessions/{id}/grid` | Get 2D grid |
| GET | `/api/sessions/{id}/snapshots` | List snapshots |
| GET | `/api/sessions/{id}/snapshots/{step}` | Get snapshot |
| POST | `/api/sessions/{id}/snapshots` | Save snapshot |

### Create session

```json
POST /api/sessions/
{
  "name": "My Experiment",
  "rule_id": 1,
  "board_width": 64,
  "board_height": 64,
  "neighbourhood": "moore8",
  "num_states": 3,
  "seed_config": {
    "type": "empty"
  },
  "metrics_enabled": ["density", "entropy"]
}
```

Seed config types: `empty`, `single`, `random`, `pattern`.

Random example:

```json
{
  "type": "random",
  "density": 0.3,
  "states": [1, 2]
}
```

## Metrics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/metrics/` | List available metrics |

```json
[
  {
    "name": "density",
    "description": "Fraction of non-zero cells",
    "category": "structure",
    "is_builtin": true
  }
]
```

## WebSocket simulation

```
WS /api/sim/ws/{session_id}
```

See [Architecture — WebSocket protocol](architecture.md#websocket-protocol).

### JavaScript client

```javascript
const sim = new SimulationClient(sessionId, onFrame, onStatus);
sim.connect();
sim.start(currentGrid);  // optional grid on start
sim.paint(x, y, state);
sim.pause();
```

Defined in `web/static/js/app.js`.

## Page routes

| GET | Serves |
|-----|--------|
| `/` | `landing.html` |
| `/dashboard` | `dashboard.html` |
| `/simulation/{id}` | `sim.html` |

Legacy `.html` URLs redirect to clean paths.

## Error responses

REST errors return FastAPI standard JSON:

```json
{"detail": "Session not found"}
```

WebSocket errors:

```json
{"type": "error", "message": "..."}
```
