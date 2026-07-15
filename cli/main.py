"""CLI entry point for CA Lab.

Usage:
    ca-lab run -f configs/Conway.yaml          # Run from YAML config
    ca-lab run -f configs/Conway.yaml --headless  # Run without renderer
    ca-lab run -f configs/Conway.yaml --renderer pygame  # Override renderer
    ca-lab play --rule Conway --width 64 --height 64  # Quick play
    ca-lab list-rules                           # List all rules
    ca-lab list-metrics                         # List all metrics
    ca-lab validate --rule Conway --steps 100   # Validate rule
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
import yaml

app = typer.Typer(help="CA Lab — Cellular Automaton Laboratory")


def _load_config(path: Path) -> dict[str, Any]:
    """Load experiment config from YAML."""
    with open(path) as f:
        return yaml.safe_load(f)


def _build_simulator(config: dict[str, Any]):
    """Build a simulator from a config dict."""
    from ca_engine.config.experiment import ExperimentConfig
    from ca_engine.core.simulator import Simulator
    from ca_engine.core.board import Board
    from ca_engine.core.neighbourhood import Neighbourhood
    from ca_engine.core.palette import Palette
    from ca_engine.core.seed import SeedConfig
    from ca_engine.rules.legacy_loader import LegacyRuleLoader
    from ca_engine.metrics.registry import MetricRegistry
    import numpy as np

    # Validate config
    exp = ExperimentConfig.model_validate(config)

    # Load rule
    loader = LegacyRuleLoader()
    table = loader.load(exp.rule, num_states=exp.num_states)

    # Setup board
    board = Board(exp.width, exp.height)
    neighbourhood = Neighbourhood.from_name(exp.neighbourhood)
    palette = Palette.default(exp.num_states) if exp.palette is None else Palette.from_file(exp.palette)

    # Create simulator
    rng = np.random.default_rng(exp.global_seed)
    sim = Simulator(board, table, neighbourhood, palette, rng)
    sim.reset(SeedConfig.model_validate(exp.seed.model_dump()))

    # Attach metrics
    registry = MetricRegistry()
    for metric_name in exp.metrics:
        if isinstance(metric_name, dict):
            metric = registry.get(metric_name)
        else:
            metric = registry.get(metric_name)
        metric.on_init((exp.height, exp.width), exp.num_states)
        sim.attach_metric(metric)

    return sim, exp, table


@app.command()
def run(
    config_file: Path = typer.Option(..., "--file", "-f", help="Experiment YAML config file"),
    renderer: str | None = typer.Option(None, "--renderer", "-r", help="Override renderer (pygame, terminal, headless)"),
    headless: bool = typer.Option(False, "--headless", "--no-render", help="Run without any renderer (data export only)"),
) -> None:
    """Run an experiment from a YAML config file.

    Examples:
        ca-lab run -f configs/Conway.yaml
        ca-lab run -f configs/Conway.yaml --headless
        ca-lab run -f configs/Conway.yaml --renderer terminal
    """
    from ca_engine.logging.metrics_logger import MetricsLogger
    from ca_engine.logging.provenance import Provenance

    config = _load_config(config_file)
    sim, exp, table = _build_simulator(config)

    # Determine renderer
    chosen_renderer = None
    if headless:
        chosen_renderer = "headless"
    elif renderer:
        chosen_renderer = renderer
    else:
        chosen_renderer = config.get("renderer", "pygame")

    # Setup logging
    log_config = exp.log
    logger = None
    if log_config.enabled:
        logger = MetricsLogger(log_config.output_dir, log_config.format)

    prov = Provenance(
        exp.name,
        exp.rule,
        table.source_hash,
        Provenance.hash_config(config),
        exp.global_seed,
    )

    # Run
    if chosen_renderer == "pygame":
        _run_pygame(sim, exp, logger, prov)
    elif chosen_renderer == "terminal":
        _run_terminal(sim, exp, logger, prov)
    elif chosen_renderer == "headless":
        _run_headless(sim, exp, logger, prov)
    else:
        typer.echo(f"Unknown renderer: {chosen_renderer}")
        raise typer.Exit(1)


def _run_pygame(sim, exp, logger, prov):
    """Run with Pygame renderer."""
    from ca_engine.renderers.pygame_renderer import PygameRenderer
    from ca_engine.core.palette import Palette

    palette = Palette.default(exp.num_states) if exp.palette is None else Palette.from_file(exp.palette)
    renderer = PygameRenderer(
        (exp.height, exp.width),
        palette.colors,
        exp.cell_size,
        title=f"CA Lab — {exp.rule}",
        show_grid=exp.show_grid,
    )

    try:
        for step in range(1, exp.steps + 1):
            action = renderer.render(sim.board.data, sim._collect_metrics())

            if action == "quit":
                typer.echo("User quit.")
                break
            elif action == "reset":
                sim.reset()
                continue
            elif action == "step":
                sim.step()
            elif action == "pause":
                # Keep rendering but don't step
                continue
            else:
                sim.step()

            if logger and step % exp.log.metrics_every == 0:
                logger.on_step(step, sim._collect_metrics())
    finally:
        renderer.close()

    if logger:
        logger.on_experiment_end()
        prov.save(exp.log.output_dir)
        typer.echo(f"Results saved to {exp.log.output_dir}")


def _run_terminal(sim, exp, logger, prov):
    """Run with terminal renderer (ASCII)."""
    import time
    for step in range(1, exp.steps + 1):
        sim.step()
        metrics = sim._collect_metrics()

        # Clear screen and print
        print("\033[2J\033[H", end="")
        print(f"Step {step}/{exp.steps} | Rule: {exp.rule}")
        print("-" * 40)
        for key, value in metrics.items():
            print(f"  {key}: {value:.4f}")
        print("-" * 40)

        # Simple ASCII grid preview (first 20x20)
        grid = sim.board.data
        h, w = grid.shape
        preview_h = min(20, h)
        preview_w = min(40, w)
        for y in range(preview_h):
            row = ""
            for x in range(preview_w):
                row += "█" if grid[y, x] > 0 else " "
            print(row)

        if logger and step % exp.log.metrics_every == 0:
            logger.on_step(step, metrics)

        time.sleep(0.1)

    if logger:
        logger.on_experiment_end()
        prov.save(exp.log.output_dir)
        typer.echo(f"Results saved to {exp.log.output_dir}")


def _run_headless(sim, exp, logger, prov):
    """Run without renderer (batch mode)."""
    from tqdm import tqdm
    for step in tqdm(range(1, exp.steps + 1), desc="Running simulation"):
        sim.step()
        if logger and step % exp.log.metrics_every == 0:
            logger.on_step(step, sim._collect_metrics())

    if logger:
        logger.on_experiment_end()
        prov.save(exp.log.output_dir)
        typer.echo(f"Results saved to {exp.log.output_dir}")

    # Print final metrics
    metrics = sim._collect_metrics()
    typer.echo(f"\nFinal metrics after {exp.steps} steps:")
    for key, value in metrics.items():
        typer.echo(f"  {key}: {value:.6f}")


@app.command()
def play(
    rule: str = typer.Option("Conway", "--rule", help="Rule name"),
    width: int = typer.Option(64, "--width", "-w"),
    height: int = typer.Option(64, "--height", "-h"),
    cell_size: int = typer.Option(8, "--cell-size", "-c"),
    seed: str = typer.Option("single", "--seed", "-s"),
    neighbourhood: str = typer.Option("moore8", "--neighbourhood", "-n"),
    renderer: str = typer.Option("pygame", "--renderer", "-r"),
    states: int = typer.Option(2, "--states", "-k"),
    density: float = typer.Option(0.0, "--density", "-d"),
) -> None:
    """Quick-play a rule without a config file.

    Examples:
        ca-lab play --rule Conway
        ca-lab play --rule 413 --states 5 --seed random --density 0.3
        ca-lab play --rule Conway --width 128 --height 128 --cell-size 4
    """
    from ca_engine.core.simulator import Simulator
    from ca_engine.core.board import Board
    from ca_engine.core.neighbourhood import Neighbourhood
    from ca_engine.core.palette import Palette
    from ca_engine.core.seed import SeedConfig
    from ca_engine.rules.legacy_loader import LegacyRuleLoader
    import numpy as np

    loader = LegacyRuleLoader()
    table = loader.load(rule, num_states=states)
    board = Board(width, height)
    nbh = Neighbourhood.from_name(neighbourhood)
    palette = Palette.default(states)
    rng = np.random.default_rng()
    sim = Simulator(board, table, nbh, palette, rng)

    if seed == "random" and density > 0:
        sim.reset(SeedConfig(type="random", density=density, states=list(range(1, states))))
    else:
        sim.reset(SeedConfig(type=seed, state=1))

    if renderer == "pygame":
        from ca_engine.renderers.pygame_renderer import PygameRenderer
        pygame_renderer = PygameRenderer(
            (height, width),
            palette.colors,
            cell_size,
            title=f"CA Lab — {rule}",
        )
        try:
            pygame_renderer.run(sim)
        finally:
            pygame_renderer.close()
    else:
        typer.echo("Only pygame renderer is supported for quick-play.")
        raise typer.Exit(1)


@app.command()
def list_rules() -> None:
    """List all available rules."""
    from ca_engine.rules.legacy_loader import LegacyRuleLoader

    loader = LegacyRuleLoader()
    rules = loader.list_rules()
    typer.echo(f"Available rules ({len(rules)}):")
    for rule in rules:
        typer.echo(f"  - {rule}")


@app.command()
def list_metrics() -> None:
    """List all available metrics."""
    from ca_engine.metrics.registry import MetricRegistry

    registry = MetricRegistry()
    typer.echo(f"Available metrics ({len(registry.names())}):")
    for meta in registry.list():
        typer.echo(f"  - {meta.name}: {meta.description}")


@app.command()
def list_configs() -> None:
    """List all available experiment configs."""
    configs_dir = Path("configs")
    if not configs_dir.exists():
        typer.echo("No configs directory found.")
        return

    configs = sorted(configs_dir.glob("*.yaml"))
    typer.echo(f"Available configs ({len(configs)}):")
    for path in configs:
        if path.name.startswith("_"):
            continue
        typer.echo(f"  - {path.name}")


@app.command()
def convert_rules(
    source_dir: Path | None = typer.Option(None, "--source", help="Source .txt rules directory"),
    output_dir: Path | None = typer.Option(None, "--output", help="Output .yaml directory"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing YAML files"),
) -> None:
    """Convert legacy .txt rule files to YAML format.

    Examples:
        ca-lab convert-rules
        ca-lab convert-rules --source reference_code/rules --output rules --overwrite
    """
    from ca_engine.rules.yaml_loader import RuleConverter

    converter = RuleConverter(source_dir, output_dir)
    generated = converter.convert_all(overwrite=overwrite)

    typer.echo(f"Converted {len(generated)} rules to YAML:")
    for path in generated:
        typer.echo(f"  {path.name}")


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port"),
    reload: bool = typer.Option(True, "--reload/--no-reload", help="Auto-reload on code changes"),
) -> None:
    """Launch the CA Lab Web UI (FastAPI + SQLite + WebSocket).

    Examples:
        ca-lab web
        ca-lab web --port 8080
        ca-lab web --host 0.0.0.0 --no-reload
    """
    import uvicorn
    typer.echo(f"Starting CA Lab Web UI at http://{host}:{port}/")
    uvicorn.run("app:app", host=host, port=port, reload=reload)


@app.command()
def evolve(
    target: Path = typer.Option(..., "--target", "-t", help="Target image PNG file"),
    rule: str | None = typer.Option(None, "--rule", help="Seed rule name"),
    width: int = typer.Option(32, "--width", "-w"),
    height: int = typer.Option(32, "--height", "-h"),
    states: int = typer.Option(2, "--states", "-k"),
    generations: int = typer.Option(50, "--generations", "-g"),
    population: int = typer.Option(20, "--population", "-p"),
    mutation: float = typer.Option(0.05, "--mutation", "-m"),
    headless: bool = typer.Option(False, "--headless", help="Run without matplotlib visualization"),
    output: Path = typer.Option(Path("evolved_rule.yaml"), "--output", "-o"),
) -> None:
    """Evolve a CA rule to match a target image using genetic algorithm.

    Examples:
        ca-lab evolve -t docs/sample.png --generations 100
        ca-lab evolve -t target.png --rule Conway --headless -o best.yaml
    """
    from PIL import Image
    import numpy as np
    from ca_engine.evolution.chromosome import Chromosome
    from ca_engine.evolution.fitness import FitnessEvaluator
    from ca_engine.evolution.pipeline import EvolutionPipeline
    from ca_engine.rules.legacy_loader import LegacyRuleLoader

    img = Image.open(target).convert("RGB")
    img = img.resize((width, height), Image.Resampling.NEAREST)
    arr = np.array(img)
    gray = np.mean(arr, axis=2)
    target_grid = (gray / 255.0 * (states - 1)).astype(np.uint8)

    seed_rule = None
    if rule:
        loader = LegacyRuleLoader()
        table = loader.load(rule, num_states=states)
        seed_rule = Chromosome.from_rule_yaml(table.to_yaml(), states, "moore8")

    evaluator = FitnessEvaluator(
        target_grid=target_grid,
        weights={"similarity": 0.6, "metrics": 0.2, "simplicity": 0.2},
        steps=10,
        width=width,
        height=height,
    )
    pipeline = EvolutionPipeline(
        population_size=population,
        generations=generations,
        mutation_rate=mutation,
        fitness_evaluator=evaluator,
        seed_rule=seed_rule,
    )

    if not headless:
        try:
            import matplotlib.pyplot as plt
            fig, axes = plt.subplots(1, 2, figsize=(8, 4))
        except ImportError:
            headless = True

    best_ever = None
    for result in pipeline.run():
        if result.get("type") == "evolution":
            gen = result["generation"]
            best = result["best_fitness"]
            best_ever = result["best_fitness_ever"]
            if gen % 10 == 0 or gen == generations:
                typer.echo(f"Generation {gen}: best={best:.4f} ever={best_ever:.4f}")
            if not headless and gen % 5 == 0:
                sim = result["best_chromosome"].to_simulator(width, height)
                for _ in range(5):
                    sim.step()
                axes[0].imshow(target_grid, cmap="gray", vmin=0, vmax=states - 1)
                axes[0].set_title("Target")
                axes[1].imshow(sim.board.data, cmap="gray", vmin=0, vmax=states - 1)
                axes[1].set_title(f"Gen {gen} (fit={best:.3f})")
                plt.pause(0.01)

    if pipeline.best_ever:
        yaml_text = pipeline.best_ever.to_yaml()
        with open(output, "w") as f:
            f.write(yaml_text)
        typer.echo(f"Evolution complete. Best fitness: {pipeline.best_fitness_ever:.4f}")
        typer.echo(f"Best rule saved to {output}")
    else:
        typer.echo("Evolution did not produce a valid rule.")
        raise typer.Exit(1)


@app.command()
def validate(
    rule: str = typer.Option("Conway", "--rule", help="Rule to validate"),
    steps: int = typer.Option(100, "--steps", help="Number of steps"),
    config: Path | None = typer.Option(None, "--config", "-f", help="Config file to validate"),
) -> None:
    """Validate a rule or config by running it for N steps."""
    if config:
        cfg = _load_config(config)
        _, exp, _ = _build_simulator(cfg)
        typer.echo(f"Validating config: {config}")
        typer.echo(f"  Rule: {exp.rule}")
        typer.echo(f"  Board: {exp.width}x{exp.height}")
        typer.echo(f"  Neighbourhood: {exp.neighbourhood}")
        typer.echo(f"  Steps: {steps}")
    else:
        from ca_engine.core.simulator import Simulator
        from ca_engine.core.board import Board
        from ca_engine.core.neighbourhood import Neighbourhood
        from ca_engine.core.palette import Palette
        from ca_engine.core.seed import SeedConfig
        from ca_engine.rules.legacy_loader import LegacyRuleLoader

        loader = LegacyRuleLoader()
        table = loader.load(rule, num_states=2)
        board = Board(32, 32)
        sim = Simulator(board, table, Neighbourhood.N8, Palette.default(2))
        sim.reset(SeedConfig(type="single", state=1))

        for _ in range(steps):
            sim.step()

        import numpy as np
        typer.echo(f"Rule '{rule}' validated: {steps} steps completed.")
        typer.echo(f"Final live cells: {np.count_nonzero(board.data)}")


if __name__ == "__main__":
    app()
