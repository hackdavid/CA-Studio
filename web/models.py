"""Pydantic models for API request/response."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RuleCreate(BaseModel):
    name: str
    yaml_content: str
    description: str = ""
    category: str = "custom"


class RuleOut(BaseModel):
    id: int
    name: str
    yaml_content: str
    is_builtin: bool
    is_editable: bool
    description: str
    category: str
    created_at: str

    class Config:
        from_attributes = True


class RuleUpdate(BaseModel):
    name: str | None = None
    yaml_content: str | None = None
    description: str | None = None
    category: str | None = None


class SessionCreate(BaseModel):
    name: str
    rule_id: int
    board_width: int = 64
    board_height: int = 64
    neighbourhood: str = "moore8"
    num_states: int = 2
    seed_config: dict[str, Any] = Field(default_factory=dict)
    metrics_enabled: list[str] = Field(default_factory=lambda: ["density", "entropy"])


class SessionOut(BaseModel):
    id: int
    name: str
    rule_id: int
    rule_name: str = ""
    board_width: int
    board_height: int
    neighbourhood: str
    num_states: int
    seed_config: dict[str, Any]
    current_step: int
    status: str
    metrics_enabled: list[str]
    created_at: str

    class Config:
        from_attributes = True


class SessionUpdate(BaseModel):
    name: str | None = None
    current_grid: list[list[int]] | None = None
    current_step: int | None = None
    status: str | None = None


class SnapshotOut(BaseModel):
    id: int
    session_id: int
    step_number: int
    metrics_json: dict[str, Any] | None
    created_at: str

    class Config:
        from_attributes = True


class MetricCreate(BaseModel):
    name: str
    formula: str
    description: str = ""


class MetricOut(BaseModel):
    id: int
    name: str
    formula: str
    description: str
    is_builtin: bool
    created_at: str

    class Config:
        from_attributes = True


class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[dict[str, Any]]
    warnings: list[dict[str, Any]]


class ExportRequest(BaseModel):
    session_id: int
    step_number: int | None = None
    format: str = "yaml"  # yaml, csv, png


class SimulationControl(BaseModel):
    action: str  # start, pause, step, reset, paint, speed
    session_id: int | None = None
    count: int | None = None
    x: int | None = None
    y: int | None = None
    state: int | None = None
    fps: int | None = None
