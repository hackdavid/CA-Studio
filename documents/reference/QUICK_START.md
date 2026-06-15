# CA Lab - Quick Start Guide

> **Updated docs:** Prefer [../README.md](../README.md) and [../getting-started/quick-start.md](../getting-started/quick-start.md)

## 🚀 Starting the Server

### Option 1: Using the Start Script (Recommended)
```bash
python start.py
```

### Option 2: Direct Uvicorn Command
```bash
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### Option 3: Using the CLI
```bash
ca-lab web
```

## 🌐 Accessing the Application

Once the server is running, open your browser and navigate to:

### **Landing Page** (Start Here!)
```
http://127.0.0.1:8000/landing
```
Professional landing page showcasing research features, education section, and live Conway's Life preview.

### **Dashboard** (Management Hub)
```
http://127.0.0.1:8000/dashboard
```
Central dashboard for:
- Creating new sessions
- Managing rules (Built-in: Conway, Wolfram, Brian's Brain)
- Managing metrics (Density, Entropy, Activity)
- Viewing session history

### **Simulation** (Direct Access)
```
http://127.0.0.1:8000/simulation
```
Real-time cellular automata simulation with:
- 10%-80%-10% layout (controls - canvas - metrics)
- Dynamic cell sizing (adapts to board size)
- Real-time metrics tracking
- Interactive drawing tools

## 🔧 First-Time Setup

### 1. Database Initialization
The database is automatically created on first startup. If you encounter issues:

```bash
# Fix existing database schema
python fix_database.py

# Or delete and recreate (WARNING: loses all data)
rm ca_lab.db ca_lab.db-shm ca_lab.db-wal
python start.py
```

### 2. Dependencies
Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

Required packages:
- FastAPI
- Uvicorn
- SQLAlchemy
- aiosqlite
- numpy
- PyYAML
- (and others in requirements.txt)

## 📱 User Workflows

### Creating Your First Session

1. **Start Server**: `python start.py`
2. **Open Dashboard**: http://127.0.0.1:8000/dashboard
3. **Click "New Session"** button (top of left sidebar)
4. **Configure Session**:
   - Enter session name (e.g., "My First CA Experiment")
   - Select rule (Conway's Life is pre-selected)
   - Set board dimensions (default: 64×64)
   - Choose metrics to track (Density + Entropy recommended)
   - Select seed configuration (Random 30% density)
5. **Click "Create Session"** → Redirects to simulation page
6. **Run Simulation**: Click "▶ Start" button

### Running a Simulation

1. **Controls** (left panel):
   - **Start**: Begin real-time simulation
   - **Pause**: Pause at current step
   - **Step**: Advance one step at a time
   - **Reset**: Return to initial seed state
   
2. **Speed Control**: Adjust slider (10ms-500ms between steps)

3. **Drawing Tools**:
   - **Pencil**: Draw alive cells on canvas
   - **Eraser**: Clear cells
   
4. **View Options**:
   - **Grid Lines**: Toggle cell borders (ON by default)
   - **Cell Numbers**: Show state numbers (OFF by default)

5. **Metrics** (right panel):
   - **Density**: Fraction of alive cells
   - **Entropy**: Shannon entropy measure
   - **Activity**: Percentage of cells changed per step
   - **Stability**: Pattern stability indicator

6. **Export Options** (top bar):
   - **Save**: Save current session state
   - **Export**: Download canvas as PNG image

### Managing Rules

1. **Dashboard → Rules Tab**
2. **Search** for existing rules or browse list
3. **Built-in Rules**:
   - Conway's Life (B3/S23)
   - Wolfram Rule 110
   - Brian's Brain
   - (More rules in `rules/` directory)
4. **Create New Rule**: Click "Create New Rule" button

### Managing Metrics

1. **Dashboard → Metrics Tab**
2. **Built-in Metrics**:
   - **Density**: Fraction of non-zero cells
   - **Entropy**: Shannon entropy over all states
   - **Activity Rate**: Cells changed per step (custom)
3. **Create New Metric**: Click "Create New Metric" button

## 🎨 Design Features

### Responsive Layout
- **Desktop (1024px+)**: Full 10%-80%-10% layout
- **Tablet (768px)**: 2-column grid, collapsible sidebar
- **Mobile (375px)**: Single column, stacked panels

### Accessibility
- ✅ Keyboard navigation (Tab, Enter, Space, Arrows)
- ✅ Screen reader support (ARIA labels)
- ✅ High contrast (4.5:1 minimum)
- ✅ Reduced motion support (respects system preference)

### Animations
- Smooth transitions (150-300ms)
- Purposeful motion (state changes, feedback)
- Hover effects (cards lift, buttons scale)
- Status indicators (pulse on "Running")

## 🐛 Troubleshooting

### Server Won't Start

**Error: `sqlite3.OperationalError: table rules has no column named is_builtin`**

**Solution:**
```bash
python fix_database.py
```

**Error: `ModuleNotFoundError: No module named 'app'`**

**Solution:**
```bash
# Run from project root
cd ca_project
python start.py
```

### Database Issues

**Corrupted Database:**
```bash
# Backup (if needed)
cp ca_lab.db ca_lab.db.backup

# Delete database files
rm ca_lab.db ca_lab.db-shm ca_lab.db-wal

# Restart server (auto-recreates)
python start.py
```

**Schema Mismatch:**
```bash
python fix_database.py
```

### Canvas Not Displaying

1. Check browser console (F12) for errors
2. Ensure JavaScript is enabled
3. Try different browser (Chrome, Firefox, Edge)
4. Clear browser cache (Ctrl+Shift+Del)

### Slow Performance

**Large Board Sizes:**
- Use smaller grids (64×64 instead of 256×256)
- Reduce simulation speed (increase interval to 200-500ms)
- Disable grid lines in View Options

**Many Active Sessions:**
- Close unused simulations
- Clear old sessions from dashboard

## 📂 File Structure

```
ca_project/
├── app.py                     # Main FastAPI application
├── start.py                   # Startup script
├── web/                       # API + UI
│   ├── database.py            # Async SQLite (aiosqlite)
│   ├── models.py              # Pydantic models
│   ├── routers/               # API + WebSocket routes
│   └── static/                # Frontend files
│       ├── landing.html
│       ├── dashboard.html
│       └── sim.html
├── ca_engine/                # CA simulation engine
│   ├── core/                 # Core logic (grid, board, simulator)
│   ├── rules/                # Rule compiler + validator
│   └── metrics/              # Metric calculators
├── rules/                    # YAML rule definitions
├── design-system/            # UI/UX design system
│   └── ca-lab/
│       └── MASTER.md         # Global design rules
├── ca_lab.db                 # SQLite database
├── start_server.py           # ✨ NEW: Easy startup script
├── fix_database.py           # Database migration tool
└── requirements.txt          # Python dependencies
```

## 🎓 Next Steps

### For Researchers
1. Create custom rules in `rules/` directory (YAML format)
2. Export session data for statistical analysis
3. Save sessions with full provenance for reproducibility

### For Educators
1. Use pre-built examples (Conway, Wolfram)
2. Create assignments based on different rules
3. Students can save and share their results

### For Students
1. Experiment with different board sizes and rules
2. Track metrics to understand emergent behavior
3. Draw custom initial patterns

## 📚 Additional Resources

- **Documentation**: http://127.0.0.1:8000/docs (FastAPI auto-generated)
- **Design System**: `design-system/ca-lab/MASTER.md`
- **UX Guide**: `UX_REDESIGN_SUMMARY.md`
- **Layout Reference**: `LAYOUT_REFERENCE.md`

## 💡 Tips

- **Best Board Size**: Start with 64×64 for balanced performance
- **Recommended Speed**: 100-150ms for real-time visualization
- **Save Often**: Export important sessions as you experiment
- **Explore Rules**: Try different built-in rules to see varied behaviors
- **Combine Metrics**: Track multiple metrics to understand complex dynamics

---

**Enjoy exploring the fascinating world of cellular automata! 🧬✨**
