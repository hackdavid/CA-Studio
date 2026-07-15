"""Chromosome encoding: rule table + seed config into a flat vector."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import numpy as np

from ca_engine.core.board import Board
from ca_engine.core.neighbourhood import Neighbourhood
from ca_engine.core.palette import Palette
from ca_engine.core.seed import SeedConfig
from ca_engine.core.simulator import Simulator
from ca_engine.rules.yaml_loader import YAMLRuleLoader
from ca_engine.rules.legacy_loader import LegacyRuleLoader


@dataclass
class Chromosome:
    """A candidate solution: rule transitions + seed parameters."""

    rule_table: np.ndarray  # shape: (num_states, max_neighbors+1)
    seed_type: str = "random"
    seed_density: float = 0.3
    seed_state: int = 1
    seed_states: list[int] | None = None
    num_states: int = 2
    neighbourhood: str = "moore8"
    rule_name: str = "evolved"
    yaml_content: str = ""

    @classmethod
    def from_random(
        cls,
        num_states: int = 2,
        neighbourhood: str = "moore8",
        seed_type: str = "random",
        seed_density: float = 0.3,
    ) -> Chromosome:
        """Create a random chromosome."""
        max_neigh = 8 if neighbourhood in ("moore8", "moore9") else 4
        # Random rule table: each entry is a random state
        rule_table = np.random.randint(0, num_states, size=(num_states, max_neigh + 1), dtype=np.uint8)
        return cls(
            rule_table=rule_table,
            seed_type=seed_type,
            seed_density=seed_density,
            num_states=num_states,
            neighbourhood=neighbourhood,
        )

    @classmethod
    def from_rule_yaml(
        cls,
        yaml_content: str,
        num_states: int = 2,
        neighbourhood: str = "moore8",
    ) -> Chromosome:
        """Create a chromosome from existing rule YAML."""
        try:
            loader = YAMLRuleLoader()
            table = loader.parse_content(yaml_content)
        except Exception:
            legacy = LegacyRuleLoader()
            table = legacy.load("unknown", num_states)
        return cls(
            rule_table=table.data,
            num_states=num_states,
            neighbourhood=neighbourhood,
            yaml_content=yaml_content,
        )

    def to_simulator(self, width: int = 32, height: int = 32) -> Simulator:
        """Build a Simulator from this chromosome."""
        from ca_engine.rules.compiler import RuleTable

        board = Board(width, height)
        nbh = Neighbourhood.from_name(self.neighbourhood)
        palette = Palette.default(self.num_states)
        rule_table = RuleTable(self.rule_table.copy())
        rule_table.name = self.rule_name

        sim = Simulator(board, rule_table, nbh, palette)

        # Apply seed
        seed_cfg: dict[str, Any] = {"type": self.seed_type}
        if self.seed_type == "random":
            seed_cfg["density"] = self.seed_density
            seed_cfg["states"] = self.seed_states or list(range(1, self.num_states))
        elif self.seed_type == "single":
            seed_cfg["state"] = self.seed_state

        seed = SeedConfig.model_validate(seed_cfg)
        seed.apply(board, np.random.default_rng())
        return sim

    def to_yaml(self) -> str:
        """Convert rule table back to YAML."""
        max_neigh = self.rule_table.shape[1] - 1
        lines = [
            f"name: {self.rule_name}",
            'version: "1.0"',
            f"states: {self.num_states}",
            f"neighbourhood: {self.neighbourhood}",
            "transitions:",
        ]
        # Group transitions by (from_state, to_state)
        transition_groups: dict[tuple[int, int], list[int]] = {}
        for from_state in range(self.num_states):
            for neigh_count in range(max_neigh + 1):
                to_state = int(self.rule_table[from_state, neigh_count])
                key = (from_state, to_state)
                transition_groups.setdefault(key, []).append(neigh_count)

        for (from_state, to_state), neighbors in transition_groups.items():
            lines.append(f"  - from: [{from_state}]")
            lines.append(f"    neighbors: [{', '.join(map(str, sorted(neighbors)))}]")
            lines.append(f"    to: {to_state}")

        return "\n".join(lines) + "\n"

    def copy(self) -> Chromosome:
        """Deep copy."""
        return Chromosome(
            rule_table=self.rule_table.copy(),
            seed_type=self.seed_type,
            seed_density=self.seed_density,
            seed_state=self.seed_state,
            seed_states=list(self.seed_states) if self.seed_states else None,
            num_states=self.num_states,
            neighbourhood=self.neighbourhood,
            rule_name=self.rule_name,
            yaml_content=self.yaml_content,
        )
