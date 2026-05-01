from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RewardWeights:
    cache_hit: float = 1.0
    useful_prefetch: float = 0.7
    late_prefetch: float = -0.25
    wasted_prefetch: float = -0.6
    eviction_miss: float = -1.0


def score_transition(
    *,
    hit: bool,
    prefetch_outcome: str | None,
    eviction_caused_miss: bool,
    weights: RewardWeights = RewardWeights(),
) -> float:
    reward = weights.cache_hit if hit else 0.0

    if prefetch_outcome == "useful":
        reward += weights.useful_prefetch
    elif prefetch_outcome == "late":
        reward += weights.late_prefetch
    elif prefetch_outcome == "wasted":
        reward += weights.wasted_prefetch

    if eviction_caused_miss:
        reward += weights.eviction_miss

    return reward
