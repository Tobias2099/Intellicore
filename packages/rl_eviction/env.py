"""Environment interface and state encoders for cache eviction RL agent.

These utilities provide a minimal, dependency-free API that gem5
integration code can call to compute compact states and rewards.

Note: integration hooks (pulling live cache metadata) are not included.
This module focuses on small, fast state encoding functions.
"""
from typing import Sequence, List, Tuple
import numpy as np
from collections import deque


def encode_state_from_meta(ages: Sequence[float], freqs: Sequence[float]) -> Tuple[float, float]:
    """Encode a compact normalized state from cache metadata.

    ages: per-line recency (larger = older). freqs: per-line access frequency.
    Returns tuple (avg_age_norm, avg_freq_norm) with values in [0,1].
    """
    if len(ages) == 0:
        return 0.0, 0.0
    a = float(np.mean(ages))
    f = float(np.mean(freqs))
    # simple normalization using min/max heuristics; integration may replace with better stats
    # avoid division by zero
    a_norm = a / (a + 1.0)
    f_norm = f / (f + 1.0)
    return a_norm, f_norm


def candidate_features(ages: Sequence[float], freqs: Sequence[float]) -> List[Tuple[float, float]]:
    """Return per-candidate normalized features list matching indices.

    ages/freqs are per-line; outputs normalized to [0,1].
    """
    features = []
    if len(ages) == 0:
        return features
    # normalize by max to get [0,1]
    max_age = max(1.0, max(ages))
    max_freq = max(1.0, max(freqs))
    for a, f in zip(ages, freqs):
        features.append((float(a) / max_age, float(f) / max_freq))
    return features


def pc_hash_bucket(pc: int, buckets: int = 64) -> int:
    """Simple low-cost hash of a program counter to a small bucket.

    pc: integer program counter (or hashed PC). returns bucket index [0,buckets-1]
    """
    return int((pc * 2654435761) & 0xFFFFFFFF) % max(1, int(buckets))


class ReuseSampler:
    """Maintain a small recent-address buffer to estimate reuse distance.

    Usage: call `observe(addr)` for each access; call `distance(addr)` to
    get the reuse distance (number of unique addresses since last occurrence)
    or `None` if not seen in buffer.
    """

    def __init__(self, window: int = 128):
        self.window = int(window)
        self.buf = deque(maxlen=self.window)

    def observe(self, addr: int):
        self.buf.append(addr)

    def distance(self, addr: int):
        # compute distance (number of positions back to last occurrence)
        # scan from right (most recent) to left; returns position index or None
        for i, a in enumerate(reversed(self.buf)):
            if a == addr:
                return i  # 0 means immediate previous
        return None


def reuse_distance_bin(dist: int, bins: int = 5, max_cap: int = 1024) -> int:
    """Bin reuse distance into coarse bins.

    Bins defined exponentially: 0, 1, 2-3,4-7,8-15,... capped at max_cap.
    """
    if dist is None:
        return bins - 1
    if dist <= 0:
        return 0
    # logarithmic binning
    import math
    idx = int(min(bins - 1, math.floor(math.log2(min(dist, max_cap))) + 1))
    return idx


class EWMA:
    def __init__(self, alpha: float = 0.01, value: float = 0.0):
        self.alpha = float(alpha)
        self.value = float(value)

    def update(self, x: float) -> float:
        self.value = (1.0 - self.alpha) * self.value + self.alpha * float(x)
        return self.value



class CacheEnv:
    """Minimal environment wrapper to manage state, reward, and bookkeeping.

    This class is intentionally small: it doesn't simulate a cache, only
    provides methods to compute states and rewards from observed metadata.
    """

    def __init__(self, dram_penalty: float = 1.0, hit_reward: float = 1.0):
        self.dram_penalty = dram_penalty
        self.hit_reward = hit_reward

    def compute_state(self, ages: Sequence[float], freqs: Sequence[float]):
        return encode_state_from_meta(ages, freqs)

    def compute_candidates(self, ages: Sequence[float], freqs: Sequence[float]):
        return candidate_features(ages, freqs)

    def reward(self, hit: bool) -> float:
        return self.hit_reward if hit else -self.dram_penalty
