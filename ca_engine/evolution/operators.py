"""GA operators: mutation, crossover, selection."""

from __future__ import annotations

import numpy as np

from ca_engine.evolution.chromosome import Chromosome


def mutate(chromosome: Chromosome, rate: float = 0.05) -> Chromosome:
    """Point mutation on the rule table."""
    child = chromosome.copy()
    table = child.rule_table
    mask = np.random.random(table.shape) < rate
    # Mutate: replace with a random state
    new_values = np.random.randint(0, chromosome.num_states, size=table.shape, dtype=np.uint8)
    table[mask] = new_values[mask]
    child.rule_table = table
    return child


def crossover(parent_a: Chromosome, parent_b: Chromosome) -> Chromosome:
    """Single-point crossover on the flattened rule table."""
    child = parent_a.copy()
    flat_a = parent_a.rule_table.flatten()
    flat_b = parent_b.rule_table.flatten()
    if len(flat_a) < 2:
        return child

    point = np.random.randint(1, len(flat_a))
    child_flat = np.concatenate([flat_a[:point], flat_b[point:]])
    child.rule_table = child_flat.reshape(parent_a.rule_table.shape)
    return child


def tournament_select(population: list[Chromosome], fitness_scores: list[float], k: int = 3) -> Chromosome:
    """Tournament selection: pick k random, return the fittest."""
    indices = np.random.choice(len(population), size=min(k, len(population)), replace=False)
    best_idx = max(indices, key=lambda i: fitness_scores[i])
    return population[best_idx].copy()


def generate_initial_population(
    size: int,
    num_states: int = 2,
    neighbourhood: str = "moore8",
    seed_from_rule: Chromosome | None = None,
) -> list[Chromosome]:
    """Generate initial population of random chromosomes."""
    population = []
    for _ in range(size):
        if seed_from_rule is not None:
            # Start from a known rule and mutate it heavily
            c = mutate(seed_from_rule, rate=0.3)
            population.append(c)
        else:
            population.append(Chromosome.from_random(num_states, neighbourhood))
    return population
