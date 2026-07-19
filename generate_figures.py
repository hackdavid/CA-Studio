import os
import subprocess
import time
import signal

# Create figures directory
os.makedirs('figures', exist_ok=True)

print("=== Step 1: Generate Performance Benchmark Chart ===")
import matplotlib.pyplot as plt
import numpy as np

sizes = [64, 128, 256, 512]
times = [3.2, 8.1, 28.4, 112]
targets = [5, 20, 50, 200]

fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(sizes))
width = 0.35

bars1 = ax.bar(x - width/2, times, width, label='Measured', color='#1E3A5F')
bars2 = ax.bar(x + width/2, targets, width, label='Target', color='#059669', alpha=0.6)

ax.set_xlabel('Board Size', fontsize=11)
ax.set_ylabel('Step Time (ms)', fontsize=11)
ax.set_title('CA Studio Performance Benchmarks', fontsize=13, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels([f'{s}×{s}' for s in sizes])
ax.legend()
ax.grid(axis='y', alpha=0.3)

# Add value labels on bars
for bar in bars1:
    height = bar.get_height()
    ax.annotate(f'{height:.1f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig('figures/figure6_benchmarks.png', dpi=150)
plt.close()
print("[OK] figure6_benchmarks.png saved")

print("\n=== Step 2: Generate Mermaid Diagrams via Playwright ===")
from playwright.sync_api import sync_playwright

mermaid_html_template = """
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    body {{ margin: 0; padding: 20px; background: white; }}
    .mermaid {{ display: flex; justify-content: center; }}
  </style>
</head>
<body>
  <div class="mermaid">
{diagram}
  </div>
  <script>mermaid.initialize({{startOnLoad:true,theme:'default'}});</script>
</body>
</html>
"""

diagrams = {
    'figure1_architecture': """flowchart TB
    subgraph UI["Presentation"]
        L[landing.html]
        D[dashboard.html]
        S[sim.html + app.js]
    end
    subgraph API["FastAPI — app.py"]
        R[rules router]
        SE[sessions router]
        M[metrics router]
        SIM[simulations WS]
    end
    subgraph Data["Persistence"]
        DB[(ca_lab.db SQLite)]
    end
    subgraph Engine["ca_engine"]
        GR[Grid / Board]
        SM[Simulator]
        RL[Rule compiler]
        MT[Metrics registry]
    end
    L & D & S --> R & SE & M & SIM
    R & SE & M --> DB
    SIM --> DB
    SIM --> SM
    SM --> GR & RL & MT
    SE --> GR""",

    'figure2_websocket': """sequenceDiagram
    participant C as Client
    participant S as Server
    participant E as CA Engine
    C->>S: WS connect
    S->>C: JSON: {type:"ready"}
    C->>S: action: "start" + grid
    S->>E: load session + grid
    loop Simulation
        E->>S: next_grid + metrics
        S->>C: JSON metadata
        S->>C: binary uint8 bytes
    end
    C->>S: action: "pause"
    S->>E: stop loop
    S->>C: JSON: {type:"paused"}"""
}

with sync_playwright() as p:
    browser = p.chromium.launch()

    for name, diagram in diagrams.items():
        html = mermaid_html_template.format(diagram=diagram)
        page = browser.new_page(viewport={'width': 1200, 'height': 800})
        page.set_content(html)
        # Wait for mermaid to render
        page.wait_for_selector('.mermaid svg', timeout=10000)
        time.sleep(2)  # Extra render time
        svg = page.query_selector('.mermaid svg')
        if svg:
            svg.bounding_box()
            page.screenshot(path=f'figures/{name}.png', full_page=True)
            print(f"[OK] {name}.png saved")
        else:
            print(f"[FAIL] {name} failed to render")
        page.close()

    browser.close()

print("\n=== Step 3: Take Web App Screenshots ===")
# Start the server in background
print("Starting server...")
server_proc = subprocess.Popen(
    ['python', 'start.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
)

try:
    time.sleep(5)  # Wait for server to start

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 900})

        # Screenshot 1: Landing page
        page.goto('http://127.0.0.1:8000/')
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        page.screenshot(path='figures/figure7_landing.png', full_page=False)
        print("[OK] figure7_landing.png saved")

        # Screenshot 2: Dashboard
        page.goto('http://127.0.0.1:8000/dashboard')
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        page.screenshot(path='figures/figure3_dashboard.png', full_page=False)
        print("[OK] figure3_dashboard.png saved")

        # Screenshot 3: New Session Modal
        page.click('text=New Session')
        time.sleep(1)
        page.screenshot(path='figures/figure5_modal.png', full_page=False)
        print("[OK] figure5_modal.png saved")

        # Create a session for simulation screenshot
        page.goto('http://127.0.0.1:8000/dashboard')
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # Try to create a session
        try:
            page.click('text=New Session')
            time.sleep(0.5)
            page.fill('input[name="name"]', 'Test Session')
            # Select Conway rule
            page.click('text=Conway')
            time.sleep(0.5)
            page.click('text=Create Session')
            time.sleep(2)
            # Should redirect to simulation
            page.wait_for_url('**/simulation/**', timeout=5000)
            time.sleep(2)
            page.screenshot(path='figures/figure4_simulation.png', full_page=False)
            print("[OK] figure4_simulation.png saved")
        except Exception as e:
            print(f"[WARN] Simulation screenshot via automation failed ({e}), using existing screenshot")
            # Copy existing screenshot as fallback
            import shutil
            if os.path.exists('screenshots/sim_grid_on.png'):
                shutil.copy('screenshots/sim_grid_on.png', 'figures/figure4_simulation.png')
                print("[OK] figure4_simulation.png copied from existing screenshot")

        browser.close()

finally:
    # Kill server
    print("\nStopping server...")
    if os.name == 'nt':
        os.kill(server_proc.pid, signal.CTRL_BREAK_EVENT)
    else:
        server_proc.send_signal(signal.SIGTERM)
    server_proc.wait(timeout=5)

print("\n=== All figures generated ===")
print("Files in figures/:")
for f in sorted(os.listdir('figures')):
    print(f"  {f}")
