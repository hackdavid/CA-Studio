"""Breed pipeline: interactive population curation."""

from __future__ import annotations

from typing import Any

import numpy as np

from ca_engine.evolution.chromosome import Chromosome
from ca_engine.evolution.operators import crossover, generate_initial_population, mutate


class BreedPipeline:
    """Manages a population for interactive breeding."""

    def __init__(
        self,
        population_size: int = 9,
        num_states: int = 2,
        neighbourhood: str = "moore8",
        mutation_rate: float = 0.1,
        seed_rule: Chromosome | None = None,
    ) -> None:
        self.population_size = population_size
        self.num_states = num_states
        self.neighbourhood = neighbourhood
        self.mutation_rate = mutation_rate
        self.seed_rule = seed_rule
        self.population: list[Chromosome] = []
        self.generation = 0
        self._init_population()

    def _init_population(self) -> None:
        self.population = generate_initial_population(
            self.population_size,
            num_states=self.num_states,
            neighbourhood=self.neighbourhood,
            seed_from_rule=self.seed_rule,
        )
        self.generation = 0

    def reset(self) -> None:
        self._init_population()

    def breed_next_generation(self, parent_indices: list[int]) -> None:
        """Create next generation from selected parents."""
        if not parent_indices:
            self._init_population()
            self.generation += 1
            return

        parents = [self.population[i] for i in parent_indices if 0 <= i < len(self.population)]
        if not parents:
            parents = [self.population[0]]

        new_population: list[Chromosome] = []
        # Elitism: keep best parent
        new_population.append(parents[0].copy())

        while len(new_population) < self.population_size:
            if len(parents) >= 2:
                a, b = np.random.choice(parents, size=2, replace=False)
            else:
                a = b = parents[0]
            child = crossover(a, b)
            child = mutate(child, self.mutation_rate)
            new_population.append(child)

        self.population = new_population[: self.population_size]
        self.generation += 1

    def get_grids(self, width: int, height: int, steps: int = 5) -> list[np.ndarray]:
        """Run each candidate a few steps and return their grids."""
        grids = []
        for chrom in self.population:
            sim = chrom.to_simulator(width, height)
            for _ in range(steps):
                sim.step()
            grids.append(sim.board.data.copy())
        return grids

    def to_json(self) -> dict[str, Any]:
        return {
            "generation": self.generation,
            "population_size": self.population_size,
            "mutation_rate": self.mutation_rate,
            "population": [
                {
                    "rule_table": c.rule_table.tolist(),
                    "num_states": c.num_states,
                    "neighbourhood": c.neighbourhood,
                }
                for c in self.population
            ],
        }
