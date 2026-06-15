"""Convert all legacy .txt rule files to YAML format.

Usage:
    python scripts/convert_rules_to_yaml.py
    python scripts/convert_rules_to_yaml.py --overwrite
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ca_engine.rules.yaml_loader import RuleConverter


def main() -> None:
    print("Converting legacy .txt rules to YAML format...")
    print("=" * 50)

    converter = RuleConverter()
    generated = converter.convert_all(overwrite=False)

    print("=" * 50)
    print(f"Converted {len(generated)} rules to YAML.")
    print(f"Output directory: {converter.output_dir}")
    print()
    print("Example YAML structure:")
    print("""
name: Conway
version: "1.0"
description: "Conway's Game of Life"
states: 2
neighbourhood: moore8
transitions:
  - from: [1]
    neighbors: [2, 3]
    to: 1
  - from: [0]
    neighbors: [3]
    to: 1
""")


if __name__ == "__main__":
    main()
