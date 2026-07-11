"""Playwright E2E tests for simulation UX: square cells, zoom, and real-time metrics."""

from __future__ import annotations

import requests
from playwright.sync_api import Page, expect


CONWAY_YAML = """name: E2EConway
version: "1.0"
states: 2
neighbourhood: moore8
transitions:
- from: [1]
  neighbors: [2, 3]
  to: 1
- from: [0]
  neighbors: [3]
  to: 1
"""


def _ensure_rule(base_url: str) -> int:
    """Get or create a Conway rule for testing."""
    resp = requests.get(f"{base_url}/api/rules/")
    resp.raise_for_status()
    for rule in resp.json():
        if "conway" in rule["name"].lower() or rule["name"].lower() == "e2econway":
            return rule["id"]
    # create
    resp = requests.post(
        f"{base_url}/api/rules/",
        json={
            "name": "E2EConway",
            "yaml_content": CONWAY_YAML,
            "description": "e2e",
            "category": "custom",
        },
    )
    resp.raise_for_status()
    return resp.json()["id"]


def _create_session(base_url: str, rule_id: int, seed: str = "empty") -> int:
    """Create a simulation session and return its ID."""
    seed_map = {
        "empty": {"type": "empty"},
        "random_30": {"type": "random", "density": 0.3, "states": [1]},
        "center": {"type": "single", "state": 1, "position": "center"},
    }
    resp = requests.post(
        f"{base_url}/api/sessions/",
        json={
            "name": "E2E Test Session",
            "rule_id": rule_id,
            "board_width": 32,
            "board_height": 32,
            "neighbourhood": "moore8",
            "num_states": 2,
            "seed_config": seed_map.get(seed, {"type": "empty"}),
            "metrics_enabled": ["density", "entropy"],
        },
    )
    resp.raise_for_status()
    return resp.json()["id"]


class TestSimSquareCellsAndZoom:
    def test_cell_size_label_is_square(self, page: Page, live_server: str) -> None:
        """Cells must render as perfect squares (label shows single px value, no '×')."""
        rule_id = _ensure_rule(live_server)
        session_id = _create_session(live_server, rule_id, seed="empty")
        page.goto(f"{live_server}/simulation/{session_id}")
        page.wait_for_selector("#main-canvas")

        cell_size_label = page.locator("#info-cell-size")
        expect(cell_size_label).not_to_contain_text("×")
        expect(cell_size_label).to_contain_text("px")

    def test_zoom_in_and_out(self, page: Page, live_server: str) -> None:
        """Zoom buttons must change the zoom percentage and reset must restore 100%."""
        rule_id = _ensure_rule(live_server)
        session_id = _create_session(live_server, rule_id, seed="empty")
        page.goto(f"{live_server}/simulation/{session_id}")
        page.wait_for_selector("#main-canvas")

        zoom_display = page.locator("#zoom-display")
        expect(zoom_display).to_contain_text("100%")

        page.click("#btn-zoom-in")
        page.wait_for_timeout(150)
        expect(zoom_display).not_to_contain_text("100%")

        page.click("#btn-zoom-reset")
        page.wait_for_timeout(150)
        expect(zoom_display).to_contain_text("100%")

        page.click("#btn-zoom-out")
        page.wait_for_timeout(150)
        expect(zoom_display).not_to_contain_text("100%")


class TestSimRealTimeMetrics:
    def test_paint_updates_metrics_when_stopped(self, page: Page, live_server: str) -> None:
        """Painting a cell while the simulation is stopped must update metric cards."""
        rule_id = _ensure_rule(live_server)
        session_id = _create_session(live_server, rule_id, seed="empty")
        page.goto(f"{live_server}/simulation/{session_id}")
        page.wait_for_selector("#main-canvas")
        page.wait_for_selector("#metric-density")

        # Empty grid should have density near 0
        density = page.locator("#metric-density")
        expect(density).not_to_contain_text("—")
        initial = density.text_content()

        # Paint a cell by clicking the center of the canvas
        canvas = page.locator("#main-canvas")
        box = canvas.bounding_box()
        assert box
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

        # Wait for WebSocket metric update
        page.wait_for_timeout(600)
        updated = density.text_content()
        assert updated != initial, f"Density did not change after paint: {initial} -> {updated}"
        assert float(updated) > 0, f"Expected density > 0 after paint, got {updated}"
