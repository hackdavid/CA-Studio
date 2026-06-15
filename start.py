#!/usr/bin/env python3
"""Start CA Lab server - Consolidated application."""

import sys
import uvicorn


def main():
    """Start the CA Lab FastAPI server."""
    print("=" * 70)
    print("CA Lab - Cellular Automata Laboratory")
    print("=" * 70)
    print()
    print("Server starting at: http://127.0.0.1:8000")
    print()
    print("Pages:")
    print("  Home:       http://127.0.0.1:8000/")
    print("  Dashboard:  http://127.0.0.1:8000/dashboard")
    print("  Simulation: http://127.0.0.1:8000/simulation")
    print()
    print("API Documentation:")
    print("  Swagger UI: http://127.0.0.1:8000/api/docs")
    print("  ReDoc:      http://127.0.0.1:8000/api/redoc")
    print("  Health:     http://127.0.0.1:8000/health")
    print()
    print("WebSocket:")
    print("  Simulation: ws://127.0.0.1:8000/api/sim/ws/{session_id}")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    try:
        uvicorn.run(
            "app:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\n\n[OK] Server stopped gracefully")
        return 0
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
