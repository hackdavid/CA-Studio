"""Generate YAML experiment configs for all legacy rule files."""

from pathlib import Path
from ca_engine.rules.legacy_loader import LegacyRuleLoader
import yaml

# Map rule names to their recommended settings
RULE_CONFIGS = {
    "Conway": {
        "num_states": 2,
        "description": "Conway's Game of Life — classic B3/S23 2-state cellular automaton",
        "category": "classic",
        "seed": {"type": "random", "density": 0.3, "states": [1]},
    },
    "413": {
        "num_states": 5,
        "description": "Multi-state rule 413 — 5-state totalistic automaton",
        "category": "multi-state",
        "seed": {"type": "random", "density": 0.3, "states": [1, 2, 3, 4]},
    },
    "C6": {
        "num_states": 6,
        "description": "C6 — 6-state compact rule set",
        "category": "multi-state",
        "seed": {"type": "random", "density": 0.3, "states": [1, 2, 3, 4, 5]},
    },
    "D6": {
        "num_states": 6,
        "description": "D6 variant — 6-state rule",
        "category": "multi-state",
        "seed": {"type": "random", "density": 0.3, "states": [1, 2, 3, 4, 5]},
    },
    "DormancyA": {
        "num_states": 2,
        "description": "Dormancy behaviour A — 2-state dormancy rule",
        "category": "experimental",
        "seed": {"type": "random", "density": 0.3, "states": [1]},
    },
    "DormancyB": {
        "num_states": 2,
        "description": "Dormancy behaviour B — 2-state dormancy variant",
        "category": "experimental",
        "seed": {"type": "random", "density": 0.3, "states": [1]},
    },
    "DormancyC": {
        "num_states": 2,
        "description": "Dormancy behaviour C — 2-state dormancy variant",
        "category": "experimental",
        "seed": {"type": "random", "density": 0.3, "states": [1]},
    },
    "R413v": {
        "num_states": 5,
        "description": "R413 version 1 — 5-state rule variant",
        "category": "multi-state",
        "seed": {"type": "random", "density": 0.3, "states": [1, 2, 3, 4]},
    },
    "R413v2": {
        "num_states": 5,
        "description": "R413 version 2 — 5-state rule variant",
        "category": "multi-state",
        "seed": {"type": "random", "density": 0.3, "states": [1, 2, 3, 4]},
    },
    "TGA": {
        "num_states": 2,
        "description": "TGA rule — 2-state experimental",
        "category": "experimental",
        "seed": {"type": "random", "density": 0.3, "states": [1]},
    },
}

# Default config template
DEFAULT_CONFIG = {
    "board": [64, 64],
    "neighbourhood": "moore8",
    "steps": 500,
    "global_seed": 42,
    "metrics": ["density", "entropy"],
    "renderer": "pygame",
    "cell_size": 8,
    "show_grid": True,
    "log": {
        "enabled": True,
        "output_dir": "runs/{name}",
        "format": "csv",
        "metrics_every": 1,
        "frames_every": None,
        "animation": False,
        "provenance": True,
    },
}


def generate_config(rule_name: str, rule_info: dict) -> dict:
    """Create experiment config dict for a rule."""
    config = {
        "name": f"{rule_name.lower()}-baseline",
        "rule": rule_name,
        "num_states": rule_info["num_states"],
        "description": rule_info.get("description", f"{rule_name} rule experiment"),
        "category": rule_info.get("category", "experimental"),
    }
    config.update(DEFAULT_CONFIG)
    config["seed"] = rule_info.get("seed", {"type": "random", "density": 0.3, "states": [1]})
    config["log"]["output_dir"] = f"runs/{rule_name.lower()}-baseline"
    return config


def main():
    loader = LegacyRuleLoader()
    rules = loader.list_rules()
    configs_dir = Path("configs")
    configs_dir.mkdir(exist_ok=True)

    generated = 0
    for rule_name in rules:
        # Get rule info or use defaults
        rule_info = RULE_CONFIGS.get(rule_name, {
            "num_states": 2,
            "description": f"{rule_name} rule experiment",
            "category": "experimental",
            "seed": {"type": "random", "density": 0.3, "states": [1]},
        })

        config = generate_config(rule_name, rule_info)
        path = configs_dir / f"{rule_name}.yaml"

        with open(path, "w") as f:
            f.write(f"# {config['description']}\n")
            f.write(f"# Category: {config['category']}\n")
            f.write(f"# Generated from rule: reference_code/rules/{rule_name}.txt\n")
            f.write("\n")
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        print(f"Generated: {path}")
        generated += 1

    # Also generate a _template.yaml
    template = {
        "name": "my-experiment",
        "rule": "Conway",
        "description": "Template experiment config — copy and modify",
        "board": [64, 64],
        "neighbourhood": "moore8",
        "num_states": 2,
        "seed": {"type": "single", "state": 1, "position": "center"},
        "steps": 500,
        "global_seed": 42,
        "metrics": ["density", "entropy"],
        "renderer": "pygame",
        "cell_size": 8,
        "show_grid": True,
        "log": {
            "enabled": True,
            "output_dir": "runs/my-experiment",
            "format": "csv",
            "metrics_every": 1,
            "frames_every": None,
            "animation": False,
            "provenance": True,
        },
    }
    with open(configs_dir / "_template.yaml", "w") as f:
        f.write("# CA Lab Experiment Template\n")
        f.write("# Copy this file and modify for your experiments\n")
        f.write("# Run with: ca-lab run -f configs/your-config.yaml\n\n")
        yaml.dump(template, f, default_flow_style=False, sort_keys=False)

    print(f"\nGenerated {generated} rule configs + 1 template in {configs_dir}/")


if __name__ == "__main__":
    main()
