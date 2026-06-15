# Installation

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.10 or higher |
| pip | Latest recommended |
| OS | Windows, macOS, or Linux |
| Browser | Chrome, Firefox, or Edge (modern) |

## Clone the repository

```bash
git clone <repository-url>
cd ca_project
```

## Virtual environment (recommended)

```bash
# Windows
python -m venv env
.\env\Scripts\activate

# macOS / Linux
python3 -m venv env
source env/bin/activate
```

## Install dependencies

```bash
pip install -r requirements.txt
pip install aiosqlite
```

`aiosqlite` powers the async SQLite layer used by the web API. It may be added to `requirements.txt` in a future release.

## Verify installation

```bash
python -c "import fastapi, numpy, yaml; print('OK')"
pytest tests/ -q
```

## First run

```bash
python start.py
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

The database (`ca_lab.db`) is created automatically on first startup. Built-in rules from `rules/` and metrics are seeded into the database.

## Troubleshooting

### Port 8000 already in use

```powershell
# Windows — find and stop the process
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```

### Database schema errors

```bash
python fix_database.py
```

Or reset completely (deletes all sessions):

```bash
# Windows PowerShell
Remove-Item ca_lab.db, ca_lab.db-shm, ca_lab.db-wal -ErrorAction SilentlyContinue
python start.py
```

### Module not found

Run all commands from the project root (`ca_project/`), where `app.py` lives.
