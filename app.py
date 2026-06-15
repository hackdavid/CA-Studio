"""Consolidated CA Lab FastAPI Application.

Single entry point combining:
- Clean URL routes (no .html extensions)
- RESTful API endpoints from web/routers
- Session WebSocket simulation via web/routers/simulations
- Professional UI from web/static/
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from web.database import init_db, seed_builtin_metrics, seed_builtin_rules
from web.routers import metrics, rules, sessions, simulations

static_dir = Path(__file__).resolve().parent / "web" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize database on startup."""
    await init_db()
    await seed_builtin_rules()
    await seed_builtin_metrics()
    yield


app = FastAPI(
    title="CA Lab - Cellular Automata Laboratory",
    description="Next-generation platform for CA research, education, and experimentation",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(rules.router)
app.include_router(sessions.router)
app.include_router(metrics.router)
app.include_router(simulations.router)


@app.get("/")
async def root() -> FileResponse:
    """Serve landing page at the site root."""
    return FileResponse(static_dir / "landing.html")


@app.get("/landing")
async def landing_page() -> RedirectResponse:
    """Alias for the home page."""
    return RedirectResponse(url="/", status_code=301)


@app.get("/dashboard")
async def dashboard_page() -> FileResponse:
    """Dashboard for sessions, rules, and metrics."""
    return FileResponse(static_dir / "dashboard.html")


@app.get("/simulation")
async def simulation_page() -> FileResponse:
    """Real-time CA simulation view."""
    return FileResponse(static_dir / "sim.html")


@app.get("/simulation/{session_id}")
async def simulation_with_session(session_id: int) -> FileResponse:
    """Load a specific session in the simulation view."""
    return FileResponse(static_dir / "sim.html")


@app.get("/landing.html")
async def landing_html() -> RedirectResponse:
    return RedirectResponse(url="/", status_code=301)


@app.get("/dashboard.html")
async def dashboard_html() -> RedirectResponse:
    return RedirectResponse(url="/dashboard")


@app.get("/sim.html")
async def sim_html() -> RedirectResponse:
    return RedirectResponse(url="/simulation")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "CA Lab",
        "version": "1.0.0",
    }


@app.get("/api/info")
async def api_info() -> dict[str, Any]:
    return {
        "title": "CA Lab API",
        "version": "1.0.0",
        "endpoints": {
            "pages": {
                "/": "Home (landing page)",
                "/landing": "Redirect to /",
                "/dashboard": "Dashboard",
                "/simulation": "Simulation",
                "/simulation/{id}": "Simulation with session",
            },
            "api": {
                "/api/rules": "Rule management",
                "/api/sessions": "Session management",
                "/api/sim/ws/{session_id}": "WebSocket simulation",
                "/api/docs": "Swagger UI",
            },
        },
    }


if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("Starting CA Lab Server")
    print("=" * 70)
    print()
    print("Server: http://127.0.0.1:8000")
    print()
    print("Pages:")
    print("  Home:       http://127.0.0.1:8000/")
    print("  Dashboard:  http://127.0.0.1:8000/dashboard")
    print("  Simulation: http://127.0.0.1:8000/simulation")
    print()
    print("API Docs:   http://127.0.0.1:8000/api/docs")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
