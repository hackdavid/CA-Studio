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


class SessionMode:
    SIMULATE = "simulate"
    EVOLVE = "evolve"
    BREED = "breed"


class EvolutionConfigCreate(BaseModel):
    target_image_base64: str | None = None
    fitness_weights: dict[str, float] = Field(default_factory=lambda: {"similarity": 0.5, "metrics": 0.3, "simplicity": 0.2})
    population_size: int = 30
    generations: int = 100
    mutation_rate: float = 0.05
    evolve_rule: bool = True
    evolve_seed: bool = False
    constraints: dict[str, Any] = Field(default_factory=dict)


class SessionCreate(BaseModel):
    name: str
    rule_id: int
    board_width: int = 64
    board_height: int = 64
    neighbourhood: str = "moore8"
    num_states: int = 2
    seed_config: dict[str, Any] = Field(default_factory=dict)
    metrics_enabled: list[str] = Field(default_factory=lambda: ["density", "entropy"])
    mode: str = SessionMode.SIMULATE
    evolution_config: EvolutionConfigCreate | None = None


class EvolutionConfigOut(BaseModel):
    id: int
    session_id: int
    fitness_weights: dict[str, float]
    population_size: int
    generations: int
    mutation_rate: float
    evolve_rule: bool
    evolve_seed: bool
    constraints: dict[str, Any]
    current_generation: int
    best_fitness: float

    class Config:
        from_attributes = True


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
    mode: str
    created_at: str
    evolution_config: EvolutionConfigOut | None = None

    class Config:
        from_attributes = True


class SessionUpdate(BaseModel):
    name: str | None = None
    current_grid: list[list[int]] | None = None
    current_step: int | None = None
    status: str | None = None
    mode: str | None = None


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
    metric_type: str = "formula"
    formula: str = ""
    config: dict[str, Any] = Field(default_factory=dict)
    description: str = ""


class MetricUpdate(BaseModel):
    name: str | None = None
    metric_type: str | None = None
    formula: str | None = None
    config: dict[str, Any] | None = None
    description: str | None = None


class MetricOut(BaseModel):
    id: int
    name: str
    formula: str
    description: str
    metric_type: str = "formula"
    config: dict[str, Any] = Field(default_factory=dict)
    is_builtin: bool
    is_editable: bool = True
    created_at: str

    class Config:
        from_attributes = True


class RuleBuilderPayload(BaseModel):
    name: str
    description: str = ""
    category: str = "custom"
    states: int = 2
    neighbourhood: str = "moore8"
    transitions: list[dict[str, Any]] = Field(default_factory=list)


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


# ─── Export Models ──────────────────────────────────────────────────────────

class RenderRequest(BaseModel):
    start_step: int = 0
    end_step: int = 100
    format: str = "gif"  # gif, mp4, webm
    scale: int = 1
    overlay_metrics: bool = False
    overlay_step: bool = True
    fps: int = 10


class ExportJobOut(BaseModel):
    id: str
    session_id: int
    format: str
    start_step: int
    end_step: int
    scale: int
    status: str
    progress: int
    error: str | None = None
    created_at: str | None = None

    class Config:
        from_attributes = True


class CliStateExport(BaseModel):
    session_id: int
    include_snapshots: bool = False


class SessionEventCreate(BaseModel):
    step_number: int
    action_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
