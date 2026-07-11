"""Shared test fixtures for CA Lab."""

from __future__ import annotations

import socket
import threading
import time

import pytest
import uvicorn

from app import app


def _get_free_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.fixture(scope="session")
def live_server() -> str:
    """Start the CA Lab server in a background thread for E2E tests."""
    port = _get_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    # Wait for server to be ready
    time.sleep(1.5)
    url = f"http://127.0.0.1:{port}"
    yield url
    server.should_exit = True
