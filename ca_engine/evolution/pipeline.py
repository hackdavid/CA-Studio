"""Evolution pipeline: generation loop with progress streaming."""

from __future__ import annotations

from typing import Any

import numpy as np

from ca_engine.evolution.chromosome import Chromosome
from ca_engine.evolution.fitness import FitnessEvaluator
from ca_engine.evolution.operators import (
    crossover,
    generate_initial_population,
    mutate,
    tournament_select,
)


class EvolutionPipeline:
    """Runs a genetic algorithm to evolve CA rules."""

    def __init__(
        self,
        population_size: int = 30,
        generations: int = 100,
        mutation_rate: float = 0.05,
        tournament_k: int = 3,
        elitism: int = 2,
        fitness_evaluator: FitnessEvaluator | None = None,
        seed_rule: Chromosome | None = None,
    ) -> None:
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.tournament_k = tournament_k
        self.elitism = elitism
        self.fitness_evaluator = fitness_evaluator
        self.seed_rule = seed_rule

        self.population: list[Chromosome] = []
        self.fitness_scores: list[float] = []
        self.current_generation = 0
        self.best_ever: Chromosome | None = None
        self.best_fitness_ever = 0.0
        self.is_running = False
        self.is_paused = False

    def initialize(self) -> None:
        """Create the initial population."""
        if self.fitness_evaluator is None:
            raise ValueError("FitnessEvaluator required")

        num_states = 2
        neighbourhood = "moore8"
        if self.seed_rule:
            num_states = self.seed_rule.num_states
            neighbourhood = self.seed_rule.neighbourhood

        self.population = generate_initial_population(
            self.population_size,
            num_states=num_states,
            neighbourhood=neighbourhood,
            seed_from_rule=self.seed_rule,
        )
        self.current_generation = 0
        self.best_ever = None
        self.best_fitness_ever = 0.0
        self._evaluate_population()

    def _evaluate_population(self) -> None:
        """Evaluate all candidates."""
        self.fitness_scores = []
        for chrom in self.population:
            score = self.fitness_evaluator.evaluate(chrom)
            self.fitness_scores.append(score)

        # Track best
        best_idx = int(np.argmax(self.fitness_scores))
        if self.fitness_scores[best_idx] > self.best_fitness_ever:
            self.best_fitness_ever = self.fitness_scores[best_idx]
            self.best_ever = self.population[best_idx].copy()

    def step_generation(self) -> dict[str, Any]:
        """Run one generation. Returns progress dict."""
        if not self.population:
            self.initialize()

        self.current_generation += 1

        # Elitism: keep top N
        sorted_indices = np.argsort(self.fitness_scores)[::-1]
        new_population: list[Chromosome] = []
        for i in range(min(self.elitism, len(sorted_indices))):
            new_population.append(self.population[sorted_indices[i]].copy())

        # Breed rest
        while len(new_population) < self.population_size:
            parent_a = tournament_select(self.population, self.fitness_scores, self.tournament_k)
            parent_b = tournament_select(self.population, self.fitness_scores, self.tournament_k)
            child = crossover(parent_a, parent_b)
            child = mutate(child, self.mutation_rate)
            new_population.append(child)

        self.population = new_population[: self.population_size]
        self._evaluate_population()

        best_idx = int(np.argmax(self.fitness_scores))
        best_chrom = self.population[best_idx]

        return {
            "generation": self.current_generation,
            "best_fitness": self.fitness_scores[best_idx],
            "best_fitness_ever": self.best_fitness_ever,
            "mean_fitness": float(np.mean(self.fitness_scores)),
            "diversity": float(len(np.unique([id(c.rule_table.data.tobytes()) for c in self.population])) / len(self.population)),
            "best_chromosome": best_chrom,
        }

    def run(self) -> Any:
        """Generator that yields progress after each generation."""
        self.is_running = True
        self.initialize()

        # Yield initial state
        best_idx = int(np.argmax(self.fitness_scores))
        yield {
            "generation": 0,
            "best_fitness": self.fitness_scores[best_idx],
            "best_fitness_ever": self.best_fitness_ever,
            "mean_fitness": float(np.mean(self.fitness_scores)),
            "best_chromosome": self.population[best_idx],
        }

        for _ in range(self.generations):
            if not self.is_running:
                break
            while self.is_paused:
                yield {"type": "paused"}
            result = self.step_generation()
            result["type"] = "evolution"
            yield result

        self.is_running = False
        yield {
            "type": "done",
            "generation": self.current_generation,
            "best_fitness_ever": self.best_fitness_ever,
            "best_chromosome": self.best_ever,
        }

    def pause(self) -> None:
        self.is_paused = True

    def resume(self) -> None:
        self.is_paused = False

    def stop(self) -> None:
        self.is_running = False
