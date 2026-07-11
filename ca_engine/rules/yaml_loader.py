"""Load rules from YAML format — the modern, human-readable standard.

YAML Schema v1:
    name: str            # Rule name (e.g., "Conway")
    version: str         # Schema version (e.g., "1.0")
    description: str    # Human-readable description
    author: str         # Author / source
    states: int         # Number of states K
    neighbourhood: str # moore8, moore9, neumann, neumann_center

    # Transitions define the rule table
    transitions:
      - from: [1]           # Current state(s) — list or single int
        neighbors: [2, 3]   # Neighbour counts that trigger this
        to: 1               # Next state (int or "same" to keep current)
      - from: [0]
        neighbors: [3]
        to: 1

Legacy .txt rows like `[;1;2,3;1]` become:
    transitions:
      - from: [1]
        neighbors: [2, 3]
        to: 1
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .rule_row import RuleRow, COUNT_VALUES
from .compiler import RuleTable, compile_rule_table, rule_table_to_rows


class YAMLRuleLoader:
    """Load rules from YAML files."""

    def __init__(self, rules_dir: str | Path | None = None) -> None:
        if rules_dir is None:
            project_root = Path(__file__).resolve().parents[2]
            rules_dir = project_root / "rules"
        self.rules_dir = Path(rules_dir)

    def load(self, name: str, num_states: int | None = None) -> RuleTable:
        """Load a rule by name (without extension)."""
        # Try YAML first, then fallback to legacy .txt
        yaml_path = self.rules_dir / f"{name}.yaml"
        if yaml_path.exists():
            return self.load_file(yaml_path)

        # Fallback to legacy loader
        from .legacy_loader import LegacyRuleLoader
        return LegacyRuleLoader(self.rules_dir).load(name, num_states)

    def load_file(self, path: str | Path) -> RuleTable:
        """Load a rule from a YAML file path."""
        path = Path(path)
        with open(path) as f:
            data = yaml.safe_load(f)
        return self._parse(data, path)

    def parse_content(self, yaml_content: str) -> RuleTable:
        """Parse YAML string content into RuleTable."""
        data = yaml.safe_load(yaml_content)
        if not isinstance(data, dict):
            raise ValueError("Rule YAML must be a mapping/object")
        return self._parse(data)

    def _parse(self, data: dict[str, Any] | str, path: Path | None = None) -> RuleTable:
        """Parse YAML dict (or string content) into RuleTable."""
        if isinstance(data, str):
            parsed = yaml.safe_load(data)
            if not isinstance(parsed, dict):
                raise ValueError("Rule YAML must be a mapping/object")
            data = parsed
        name = data.get("name", path.stem if path else "unknown")
        num_states = data.get("states", data.get("num_states", 101))
        transitions = data.get("transitions", data.get("rows", []))

        rows: list[RuleRow] = []
        for t in transitions:
            row = RuleRow()
            row.name = t.get("name", "")

            # Parse 'from' field (previous states)
            prev = t.get("from", t.get("previous", []))
            if isinstance(prev, int):
                prev = [prev]
            prev_bools = [False] * num_states
            for s in prev:
                if 0 <= s < num_states:
                    prev_bools[s] = True
            row.previous = prev_bools
            row.previous_code = self._encode(prev_bools)

            # Parse 'neighbors' field (counts)
            counts = t.get("neighbors", t.get("counts", t.get("count", [])))
            if isinstance(counts, int):
                counts = [counts]
            count_bools = [False] * COUNT_VALUES
            for c in counts:
                if 0 <= c < COUNT_VALUES:
                    count_bools[c] = True
            row.count = count_bools
            row.count_code = self._encode(count_bools)

            # Parse 'to' field (next state)
            next_val = t.get("to", t.get("next", "same"))
            if next_val == "same" or next_val is None:
                row.next_same = True
                row.next = 0
            else:
                row.next_same = False
                row.next = int(next_val)

            rows.append(row)

        table = compile_rule_table(rows, num_states)
        table.name = name
        table.source = yaml.dump(data, sort_keys=False)
        return table

    @staticmethod
    def _encode(data: list[bool]) -> str:
        """Encode boolean list to comma/range string."""
        from .rule_row import encode
        return encode(data)

    def list_rules(self) -> list[str]:
        """List all available YAML rule names."""
        names = []
        for path in self.rules_dir.glob("*.yaml"):
            names.append(path.stem)
        return sorted(names)

    def save(self, table: RuleTable, path: Path, metadata: dict[str, Any] | None = None) -> None:
        """Save a RuleTable to YAML format.

        This converts the compiled table back to human-readable YAML.
        """
        from .compiler import rule_table_to_rows

        rows = rule_table_to_rows(table.table, table.num_states)
        transitions = []
        for row in rows:
            prev = [i for i, v in enumerate(row.previous) if v]
            counts = [i for i, v in enumerate(row.count) if v]
            if not prev or not counts:
                continue

            t: dict[str, Any] = {
                "from": prev,
                "neighbors": counts,
            }
            if row.next_same:
                t["to"] = "same"
            else:
                t["to"] = row.next
            transitions.append(t)

        data: dict[str, Any] = {
            "name": table.name,
            "version": "1.0",
            "states": table.num_states,
            "neighbourhood": "moore8",
            "transitions": transitions,
        }

        if metadata:
            data.update(metadata)

        with open(path, "w") as f:
            f.write(f"# {table.name}\n")
            f.write(f"# Auto-generated from rule table\n\n")
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


class RuleConverter:
    """Convert legacy .txt rules to YAML format."""

    def __init__(self, source_dir: Path | None = None, output_dir: Path | None = None) -> None:
        if source_dir is None:
            project_root = Path(__file__).resolve().parents[2]
            source_dir = project_root / "reference_code" / "rules"
        if output_dir is None:
            project_root = Path(__file__).resolve().parents[2]
            output_dir = project_root / "rules"

        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.yaml_loader = YAMLRuleLoader(self.output_dir)

    def _get_legacy_loader(self):
        """Lazy import to avoid circular dependency."""
        from .legacy_loader import LegacyRuleLoader
        return LegacyRuleLoader(self.source_dir)

    def convert_all(self, overwrite: bool = False) -> list[Path]:
        """Convert all .txt rules to .yaml.

        Returns:
            List of paths to generated YAML files.
        """
        self.output_dir.mkdir(exist_ok=True)
        generated: list[Path] = []

        for txt_path in sorted(self.source_dir.glob("*.txt")):
            yaml_path = self.output_dir / f"{txt_path.stem}.yaml"
            if yaml_path.exists() and not overwrite:
                print(f"  Skip (exists): {yaml_path.name}")
                continue

            try:
                self._convert_one(txt_path, yaml_path)
                generated.append(yaml_path)
                print(f"  Converted: {txt_path.name} -> {yaml_path.name}")
            except ValueError as e:
                print(f"  Skip (not a rule): {txt_path.name} ({e})")
                continue

        return generated

    def _convert_one(self, txt_path: Path, yaml_path: Path) -> None:
        """Convert a single .txt rule to .yaml."""
        # Load via legacy loader (lazy import)
        legacy_loader = self._get_legacy_loader()
        table = legacy_loader.load_file(txt_path)

        # Detect actual number of states used by looking at the table
        max_state = 0
        for s in range(table.num_states):
            if np.any(table.table[s] != 0):
                max_state = s
        # Also check if state 0 is used (birth rules)
        actual_states = max(2, max_state + 1)
        # Re-compile with correct num_states if needed
        if actual_states < table.num_states:
            rows = rule_table_to_rows(table.table, table.num_states)
            table = compile_rule_table(rows, actual_states)
            table.name = txt_path.stem
            table.num_states = actual_states

        # Extract metadata from the original file
        description = f"Legacy rule: {table.name}"

        metadata = {
            "description": description,
            "source": f"reference_code/rules/{txt_path.name}",
            "converted": True,
        }

        self.yaml_loader.save(table, yaml_path, metadata)

    def __repr__(self) -> str:
        return f"RuleConverter({self.source_dir} → {self.output_dir})"
