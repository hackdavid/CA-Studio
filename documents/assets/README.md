# Screenshot assets

Place UI screenshots here for documentation and the README.

## Required captures

| Filename | Page | Viewport | Notes |
|----------|------|----------|-------|
| `landing.png` | `/` | 1440×900 | Hero + live preview visible |
| `dashboard.png` | `/dashboard` | 1440×900 | Sessions tab, stats cards |
| `new-session-modal.png` | `/dashboard` | 1440×900 | Modal open with rule + metrics |
| `simulation.png` | `/simulation/{id}` | 1440×900 | Controls, canvas, metrics panels |

## How to capture

1. Start server: `python start.py`
2. Create a session (Conway, 64×64, empty seed).
3. Draw a small pattern on the canvas before capturing simulation.
4. Use browser devtools device toolbar for consistent width.
5. Save PNG files in this directory.

## Usage in docs

Reference in Markdown:

```markdown
![Dashboard](../assets/dashboard.png)
```

## Optional

- `simulation-running.gif` — short screen recording of a running CA
- `architecture-diagram.png` — exported from draw.io if needed
