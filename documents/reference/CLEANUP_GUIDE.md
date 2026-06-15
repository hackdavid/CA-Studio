# Directory Cleanup Guide

## ⚠️ Safe to Delete

The following directories/files are duplicates and can be safely deleted:

### 1. **`frontend/` directory** 
```bash
rm -rf frontend/
```
**Reason:** Empty directory, not used in consolidated app.

### 2. **Old startup scripts**
```bash
rm start_server.py
```
**Reason:** Replaced by `start.py` which uses the consolidated `app.py`.

### 3. **`fix_database.py`** (Optional - keep for reference)
```bash
# Optional: Keep this if you might need to migrate database again
# Otherwise delete:
rm fix_database.py
```
**Reason:** Database schema is now stable. Only needed for future migrations.

## 🔄 Directories to Keep

### **`web/` directory** ✅ KEEP (single web package)
- Contains API routers (rules, sessions, simulations + WebSocket)
- Contains database initialization (aiosqlite)
- Contains Pydantic models and the professional UI (`static/`)
- **Used by:** `app.py` imports `web.routers`, `web.database`, mounts `web/static`

## 📁 Final Structure

After cleanup, your structure should be:

```
ca_project/
├── app.py                    # ✨ Main consolidated application
├── start.py                  # ✨ Startup script
├── web/                      # ✅ API + UI
│   ├── database.py           # Async database (aiosqlite)
│   ├── models.py             # Pydantic models
│   ├── routers/
│   │   ├── rules.py          # /api/rules
│   │   ├── sessions.py       # /api/sessions
│   │   └── simulations.py    # /api/sim/ws/{session_id}
│   └── static/               # Professional UI
│       ├── landing.html
│       ├── dashboard.html
│       ├── sim.html
│       └── legacy/           # Archived old UI
├── ca_engine/                # ✅ Core CA simulation engine
├── rules/                    # ✅ YAML rule definitions
├── design-system/            # ✅ UI/UX design system
├── ca_lab.db                 # ✅ SQLite database
└── requirements.txt          # ✅ Python dependencies
```

## 🚀 How to Clean Up

### Option 1: Manual Cleanup
```bash
# Delete empty frontend directory
rm -rf frontend/

# Delete old startup scripts
rm start_server.py

# Optional: Delete database migration script
rm fix_database.py
```

### Option 2: Automated Cleanup Script
```bash
# Create cleanup script
cat > cleanup.sh << 'EOF'
#!/bin/bash
echo "Cleaning up duplicate directories..."

# Delete frontend (empty)
if [ -d "frontend" ]; then
    rm -rf frontend/
    echo "✓ Deleted frontend/"
fi

# Delete old startup scripts
if [ -f "start_server.py" ]; then
    rm start_server.py
    echo "✓ Deleted start_server.py"
fi

# Optional: Keep fix_database.py as backup
# Uncomment to delete:
# rm fix_database.py
# echo "✓ Deleted fix_database.py"

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Remaining structure:"
ls -d */ 2>/dev/null | grep -E "(web|ca_engine|rules)" || echo "Directories OK"
EOF

# Make executable and run
chmod +x cleanup.sh
./cleanup.sh
```

### Option 3: Windows PowerShell
```powershell
# Delete empty frontend directory
Remove-Item -Recurse -Force frontend -ErrorAction SilentlyContinue

# Delete old startup scripts
Remove-Item start_server.py -ErrorAction SilentlyContinue

# Optional: Delete fix_database.py
# Remove-Item fix_database.py -ErrorAction SilentlyContinue

Write-Host "✅ Cleanup complete!"
```

## ✅ Verification

After cleanup, verify everything works:

```bash
# 1. Start server
python start.py

# 2. Test in browser
# Visit: http://127.0.0.1:8000/landing

# 3. Check API docs
# Visit: http://127.0.0.1:8000/api/docs

# 4. Test health endpoint
curl http://127.0.0.1:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "CA Lab",
  "version": "1.0.0"
}
```

## 🔍 Why This Structure?

### `web/` directory
- **Purpose:** API layer + static UI
- **Technology:** FastAPI routers + aiosqlite (async) + HTML/CSS/JS
- **Responsibilities:** CRUD, session management, WebSocket simulation, professional UI

### `app.py` (Consolidated)
- **Purpose:** Single entry point
- **Combines:** Routers and static files from `web/`
- **Benefits:** Clean URLs, unified application, easy deployment

## 📝 Summary

**Delete:** `frontend/`, `start_server.py`, `web_ui/` (merged into `web/`)
**Keep:** `web/`, `app.py`, `start.py`
**Result:** Single `web/` folder with no duplication ✨
