"""Load legacy rule files from the Java reference format."""

from __future__ import annotations

from pathlib import Path

from .rule_row import RuleRow
from .compiler import RuleTable, compile_rule_table


class LegacyRuleLoader:
    """Load rule files in the legacy [;previous;counts;next] format."""

    def __init__(self, rules_dir: str | Path | None = None) -> None:
        if rules_dir is None:
            # Default: look for rules/ relative to project root
            project_root = Path(__file__).resolve().parents[2]
            rules_dir = project_root / "rules"
        self.rules_dir = Path(rules_dir)

    def load(self, name: str, num_states: int = 101) -> RuleTable:
        """Load a rule by name (without extension).

        Tries YAML first, then falls back to legacy .txt format.

        Args:
            name: Rule name, e.g., "Conway".
            num_states: Number of states K (used only for .txt fallback).

        Returns:
            Compiled RuleTable.
        """
        # 1. Try YAML first (modern format)
        yaml_path = self.rules_dir / f"{name}.yaml"
        if yaml_path.exists():
            from .yaml_loader import YAMLRuleLoader
            return YAMLRuleLoader(self.rules_dir).load_file(yaml_path)

        # 2. Try legacy .txt
        txt_path = self.rules_dir / f"{name}.txt"
        if txt_path.exists():
            return self.load_file(txt_path, num_states)

        # 3. Try reference_code directory
        ref_yaml = self.rules_dir.parent / "reference_code" / "rules" / f"{name}.yaml"
        if ref_yaml.exists():
            from .yaml_loader import YAMLRuleLoader
            return YAMLRuleLoader(ref_yaml.parent).load_file(ref_yaml)

        ref_txt = self.rules_dir.parent / "reference_code" / "rules" / f"{name}.txt"
        if ref_txt.exists():
            return self.load_file(ref_txt, num_states)

        raise FileNotFoundError(f"Rule not found: {name}.yaml or {name}.txt")

    def load_file(self, path: str | Path, num_states: int = 101) -> RuleTable:
        """Load a rule file from a specific path."""
        path = Path(path)
        source = path.read_text()
        rows = self.parse_source(source, num_states)
        table = compile_rule_table(rows, num_states)
        table.name = path.stem
        table.source = source
        return table

    def parse_source(self, source: str, num_states: int = 101) -> list[RuleRow]:
        """Parse rule text into RuleRow objects."""
        rows: list[RuleRow] = []
        for line in source.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                row = RuleRow.from_string(line, num_states)
                rows.append(row)
            except ValueError as e:
                raise ValueError(f"Failed to parse rule line: {line!r}") from e
        return rows

    def list_rules(self) -> list[str]:
        """List all available rule names (YAML + legacy .txt)."""
        names = set()
        # YAML rules (modern)
        for path in self.rules_dir.glob("*.yaml"):
            names.add(path.stem)
        # Legacy .txt rules
        for path in self.rules_dir.glob("*.txt"):
            names.add(path.stem)
        # Also check reference_code
        ref_dir = self.rules_dir.parent / "reference_code" / "rules"
        if ref_dir.exists():
            for path in ref_dir.glob("*.yaml"):
                names.add(path.stem)
            for path in ref_dir.glob("*.txt"):
                names.add(path.stem)
        return sorted(names)
