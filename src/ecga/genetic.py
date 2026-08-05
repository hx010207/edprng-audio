"""
Layer 2 Certification: Genetic Algorithm Search with Hard Lyapunov Exponent Culling.

Paper Section 3.8 & Section 5.2 (Eq. 9 & Eq. 10):
  Objective (Eq. 9):
    F(theta) = w1 * H(theta) + w2 * NIST(theta) + w3 * lambda1(theta)
  Hard constraint (Eq. 10):
    lambda1(theta) > 0 (any candidate with lambda1 <= 0 is culled outright).

  Method for lambda1 estimation: Wolf et al. (1985) divergence algorithm.
  Population size: 50, max generations: 100, crossover prob: 0.8, mutation sigma: 0.01.
  Weights: w1 = 1.0, w2 = 1.0, w3 = 0.5.
"""

import math
import random
from typing import Callable, List, Tuple

from ecga.hyperchaos import HyperchaoticGenerator, rk4_step

DEFAULT_W1 = 1.0
DEFAULT_W2 = 1.0
DEFAULT_W3 = 0.5


def wolf_lyapunov_exponent(
    theta: Tuple[float, float, float, float, float],
    initial_state: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    h: float = 0.01,
    warmup: int = 500,
    steps: int = 2000,
    d0: float = 1e-8,
) -> float:
    """
    Estimate the largest Lyapunov exponent lambda1 using the Wolf et al. (1985) algorithm.

    Args:
        theta: Parameter vector (a, b, c, d, e).
        initial_state: Starting state (x, y, z, w).
        h: RK4 integration step size.
        warmup: Warm-up steps discarded.
        steps: Total estimation steps.
        d0: Initial displacement vector magnitude.

    Returns:
        Estimated largest Lyapunov exponent lambda1.
    """
    # 1. Warm up fiducial state
    state = initial_state
    for _ in range(warmup):
        state = rk4_step(state, theta, h)

    # 2. Initialize perturbed state
    perturbed = (state[0] + d0, state[1], state[2], state[3])

    lyap_sum = 0.0
    for _ in range(steps):
        state = rk4_step(state, theta, h)
        perturbed = rk4_step(perturbed, theta, h)

        # Compute Euclidean distance d_k
        dist = math.sqrt(sum((s - p) ** 2 for s, p in zip(state, perturbed)))

        if dist < 1e-15:
            # Trajectories collapsed
            dist = 1e-15

        lyap_sum += math.log(dist / d0)

        # Renormalize perturbed trajectory along the same direction vector
        scale = d0 / dist
        perturbed = tuple(s + (p - s) * scale for s, p in zip(state, perturbed))

    total_time = steps * h
    lambda1 = lyap_sum / total_time
    return lambda1


def compute_byte_entropy(data: bytes) -> float:
    """Calculate Shannon byte entropy H in bits per byte (max 8.0)."""
    if not data:
        return 0.0
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    length = len(data)
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / length
            entropy -= p * math.log2(p)
    return entropy


def compute_lightweight_nist_score(data: bytes) -> float:
    """
    Lightweight NIST monobit pass score (proportion of 1-bits relative to expected 0.5).
    Scale to [0, 8] range matching entropy scale.
    """
    if not data:
        return 0.0
    total_bits = len(data) * 8
    ones = sum(bin(b).count('1') for b in data)
    ratio = ones / total_bits
    # Deviation score (1.0 for ideal ratio 0.5, lower as it deviates)
    dev = abs(ratio - 0.5)
    score = max(0.0, 8.0 * (1.0 - 2.0 * dev))
    return score


class GeneticOptimizer:
    """Genetic Algorithm Optimizer for hyperchaotic parameters with Hard Lyapunov Culling."""

    def __init__(
        self,
        pop_size: int = 50,
        max_generations: int = 100,
        crossover_prob: float = 0.8,
        mutation_sigma: float = 0.01,
        w1: float = DEFAULT_W1,
        w2: float = DEFAULT_W2,
        w3: float = DEFAULT_W3,
    ) -> None:
        self.pop_size = pop_size
        self.max_generations = max_generations
        self.crossover_prob = crossover_prob
        self.mutation_sigma = mutation_sigma
        self.w1 = w1
        self.w2 = w2
        self.w3 = w3

        # Search bounds for (a, b, c, d, e)
        self.param_bounds = [
            (10.0, 50.0),  # a
            (1.0, 10.0),   # b
            (10.0, 50.0),  # c
            (1.0, 15.0),   # d
            (0.1, 2.0),    # e
        ]

    def random_individual(self) -> Tuple[float, float, float, float, float]:
        """Generate a random parameter vector within bounds."""
        return tuple(random.uniform(low, high) for low, high in self.param_bounds)

    def evaluate_fitness(
        self, theta: Tuple[float, float, float, float, float]
    ) -> Tuple[float, float, bool]:
        """
        Evaluate candidate parameter vector theta.

        Returns:
            Tuple of (fitness_score, lambda1, survived_culling_boolean).
        """
        # Step 1: Enforce hard Lyapunov constraint (Eq. 10)
        try:
            lambda1 = wolf_lyapunov_exponent(theta, steps=1000)
        except Exception:
            lambda1 = -1.0

        if lambda1 <= 0:
            # DISCARDED IMMEDIATELY BEFORE FITNESS SCORING
            return (0.0, lambda1, False)

        # Step 2: Generate sample keystream and evaluate components
        gen = HyperchaoticGenerator(theta=theta, warmup_steps=200)
        sample_key = b"\x00" * 32
        ks_bytes = gen.generate_keystream(length=1000, ks=sample_key)

        h_score = compute_byte_entropy(ks_bytes)
        nist_score = compute_lightweight_nist_score(ks_bytes)

        # Eq. 9: F(theta) = w1*H + w2*NIST + w3*lambda1
        fitness = self.w1 * h_score + self.w2 * nist_score + self.w3 * lambda1
        return (fitness, lambda1, True)

    def run(self) -> Tuple[Tuple[float, float, float, float, float], float, List[float]]:
        """
        Run the genetic algorithm search.

        Returns:
            Tuple of (best_theta, best_fitness, list_of_generation_best_fitnesses).
        """
        population = [self.random_individual() for _ in range(self.pop_size)]
        generation_bests = []
        best_theta = None
        best_fitness = -1.0

        for gen_idx in range(self.max_generations):
            evaluated = []
            for indiv in population:
                fit, l1, survived = self.evaluate_fitness(indiv)
                evaluated.append((indiv, fit, l1, survived))

            # Sort by fitness descending
            evaluated.sort(key=lambda x: x[1], reverse=True)

            gen_best_indiv, gen_best_fit, _, _ = evaluated[0]
            generation_bests.append(gen_best_fit)

            if gen_best_fit > best_fitness:
                best_fitness = gen_best_fit
                best_theta = gen_best_indiv

            # Selection (Tournament selection among top candidates)
            survivors = [item[0] for item in evaluated if item[3]]
            if not survivors:
                # If no candidates survived culling, re-initialize population
                population = [self.random_individual() for _ in range(self.pop_size)]
                continue

            new_pop = [evaluated[0][0]]  # Elitism: keep best

            while len(new_pop) < self.pop_size:
                p1 = random.choice(survivors[:15])
                p2 = random.choice(survivors[:15])

                # Crossover
                if random.random() < self.crossover_prob:
                    child = tuple(
                        0.5 * (g1 + g2) for g1, g2 in zip(p1, p2)
                    )
                else:
                    child = p1

                # Gaussian Mutation (sigma = 0.01)
                mutated = []
                for val, (low, high) in zip(child, self.param_bounds):
                    m_val = val + random.gauss(0.0, self.mutation_sigma * (high - low))
                    m_val = max(low, min(high, m_val))
                    mutated.append(m_val)

                new_pop.append(tuple(mutated))

            population = new_pop

        return (best_theta, best_fitness, generation_bests)
