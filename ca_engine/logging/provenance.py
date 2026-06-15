"""Provenance tracking for reproducible experiments."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ca_engine import __version__


class Provenance:
    """Record experiment provenance for reproducibility."""

    def __init__(
        self,
        experiment_name: str,
        rule_path: str,
        rule_hash: str,
        config_hash: str,
        global_seed: int | None,
    ) -> None:
        self.experiment_name = experiment_name
        self.rule_path = rule_path
        self.rule_hash = rule_hash
        self.config_hash = config_hash
        self.global_seed = global_seed
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.python_version = sys.version

    def to_dict(self) -> dict[str, Any]:
        return {
            "ca_lab_version": __version__,
            "python_version": self.python_version,
            "experiment_name": self.experiment_name,
            "rule_path": self.rule_path,
            "rule_sha256": self.rule_hash,
            "config_sha256": self.config_hash,
            "global_seed": self.global_seed,
            "timestamp_utc": self.timestamp,
        }

    def save(self, output_dir: Path) -> None:
        """Save provenance JSON to output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "provenance.json"
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def hash_config(cls, config: Any) -> str:
        """Hash a configuration object for provenance."""
        data = json.dumps(config, sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()

    def __repr__(self) -> str:
        return f"Provenance({self.experiment_name}, rule={self.rule_hash[:16]}...)"
