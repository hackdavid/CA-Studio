# Quick Start

Run your first cellular automata experiment in under five minutes.

## 1. Start the server

```bash
python start.py
```

## 2. Open the dashboard

Navigate to [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard).

## 3. Create a session

1. Click **New Session** in the left sidebar.
2. Enter a name (e.g. `Conway 64x64`).
3. Search and select a rule (e.g. **Conway**).
4. Set board size (default `64 × 64`).
5. Adjust **Number of States (K)** — auto-filled from the rule; editable.
6. Choose **Initial Seed**:
   - Random (30% / 50%)
   - Center pattern
   - **Empty** — draw your own pattern on the canvas
7. Search and select **metrics** (density, entropy, etc.).
8. Click **Create Session**.

You are redirected to the simulation page for that session.

## 4. Paint and run

1. On the **left panel**, click a **color swatch** (state 0 = empty/white).
2. **Draw** on the center canvas (pause if the simulation is running).
3. Click **Start** — your drawn grid is sent as the initial state.
4. Use **Pause**, **Step**, **Reset**, and the **speed slider** as needed.
5. Watch **metrics** update in the right panel.

## 5. Export

- **Save** — snapshot to the database.
- **Export** — download the current canvas as PNG.

## Alternative: CLI

For headless or scripted runs:

```bash
ca-lab list-rules
ca-lab play --rule Conway --width 64 --height 64
ca-lab run -f configs/Conway.yaml
```

See [CA Engine](../developer/ca-engine.md) for experiment YAML format.

## Next steps

- [UI Navigation](../user-guide/navigation.md) — tour every page
- [Features](../user-guide/features.md) — rules, metrics, WebSocket protocol
- [API Reference](../developer/api-reference.md) — integrate programmatically
