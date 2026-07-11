"""API integration tests for custom rules and metrics."""

import pytest
from fastapi.testclient import TestClient

from app import app


CONWAY_YAML = """name: ApiTestRule
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


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_validate_rule_endpoint(client):
    res = client.post("/api/rules/validate", json={
        "name": "ApiTestRule",
        "yaml_content": CONWAY_YAML,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True


def test_create_and_delete_custom_rule(client):
    res = client.post("/api/rules/", json={
        "name": "ApiCustomRule",
        "yaml_content": CONWAY_YAML.replace("ApiTestRule", "ApiCustomRule"),
        "description": "test",
        "category": "custom",
    })
    assert res.status_code == 200
    rule_id = res.json()["id"]

    bad = client.post("/api/rules/", json={
        "name": "ApiCustomRule",
        "yaml_content": "invalid: [",
    })
    assert bad.status_code == 400

    client.delete(f"/api/rules/{rule_id}")


def test_metrics_templates(client):
    res = client.get("/api/metrics/templates")
    assert res.status_code == 200
    assert len(res.json()) >= 3


def test_create_validate_delete_custom_metric(client):
    import uuid
    name = f"test_combo_{uuid.uuid4().hex[:8]}"
    val = client.post("/api/metrics/validate", json={
        "name": name,
        "metric_type": "formula",
        "formula": "density + entropy",
        "config": {},
        "description": "percent alive",
    })
    assert val.status_code == 200
    assert val.json()["is_valid"] is True

    res = client.post("/api/metrics/", json={
        "name": name,
        "metric_type": "formula",
        "formula": "density + entropy",
        "config": {},
        "description": "combo",
    })
    assert res.status_code == 200, res.text
    metric_id = res.json()["id"]

    listed = client.get("/api/metrics/")
    names = [m["name"] for m in listed.json()]
    assert name in names

    client.delete(f"/api/metrics/{metric_id}")


def test_session_rejects_unknown_metric(client):
    rules = client.get("/api/rules/").json()
    assert rules
    res = client.post("/api/sessions/", json={
        "name": "Bad metrics session",
        "rule_id": rules[0]["id"],
        "metrics_enabled": ["not_a_real_metric_xyz"],
    })
    assert res.status_code == 400
