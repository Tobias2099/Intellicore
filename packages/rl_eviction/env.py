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


class TraceEnv:
    """Gym-like environment for trace-based RL training.

    Features:
    - Loads traces (CSV or list of dicts) with fields: tick, core, op, addr
    - Maintains a small set-associative cache model (params: num_sets, assoc, block_size)
    - Provides sliding-window observations of recent (delta, op) pairs
    - On misses, asks the agent to choose a victim (or accepts a provided action)
    - Computes reward by looking ahead up to `history` accesses to see if an
      evicted tag is reused (punish if so)

    Notes:
    - Actions: integer >=0 selects victim index in candidate list; use
      ACTION_LRU/ACTION_LFU/ACTION_MRU (-1,-2,-3) to select built-in policies.
    - Observation: flattened numpy array of shape (window_size*2,) containing
      (delta_norm, op) pairs for the current sliding window.
    """

    ACTION_LRU = -1
    ACTION_LFU = -2
    ACTION_MRU = -3

    def __init__(self, trace=None, window_size: int = 64, history: int = 256,
                 cache_size: int = 32 * 1024, assoc: int = 8, block_size: int = 64,
                 hit_reward: float = 1.0, dram_penalty: float = 1.0):
        self.window_size = int(window_size)
        self.history = int(history)
        self.block_size = int(block_size)
        self.assoc = int(assoc)
        self.cache_size = int(cache_size)
        # derived
        self.num_lines = self.cache_size // self.block_size
        self.num_sets = max(1, self.num_lines // self.assoc)

        # rewards
        self.hit_reward = hit_reward
        self.dram_penalty = dram_penalty

        # trace storage (list of dicts)
        self.trace = []
        if trace is not None:
            self.load_trace(trace)

        # internal state
        self.ptr = 0
        self.cache = [list() for _ in range(self.num_sets)]  # list of entries per set
        # each entry: dict(tag=int, last_touch=int, freq=int)
        self.reuse_samplers = [ReuseSampler(window=max(64, self.window_size)) for _ in range(self.num_sets)]

    def load_trace(self, trace_source):
        """Load a trace from CSV path or an in-memory list.

        Expected CSV columns: tick,core,op,addr (hex or decimal). `op` should
        be 'R'/'READ' or 'W'/'WRITE' or 0/1.
        """
        data = []
        if isinstance(trace_source, str):
            # assume CSV
            import csv
            with open(trace_source, "r") as f:
                rdr = csv.DictReader(f)
                for row in rdr:
                    try:
                        tick = int(row.get("tick", row.get("Tick", 0)))
                        core = int(row.get("core", row.get("core_id", 0)))
                        op = row.get("op", row.get("Op", "R"))
                        op = 0 if str(op).upper().startswith("R") else 1
                        addr_s = row.get("addr", row.get("address", "0"))
                        addr = int(addr_s, 0) if isinstance(addr_s, str) and addr_s.startswith("0x") else int(addr_s)
                    except Exception:
                        continue
                    data.append({"tick": tick, "core": core, "op": op, "addr": addr})
        elif isinstance(trace_source, list):
            data = trace_source
        else:
            # assume numpy structured array
            import numpy as _np
            arr = trace_source
            for r in arr:
                addr = int(r["addr"]) if "addr" in r.dtype.names else int(r[3])
                data.append({"tick": int(r["tick"]), "core": int(r["core"]), "op": int(r["op"]), "addr": addr})

        self.trace = data
        self.ptr = 0
        # reset cache
        self.cache = [list() for _ in range(self.num_sets)]

    def _addr_to_set_tag(self, addr: int):
        line_addr = addr // self.block_size
        set_idx = int(line_addr % self.num_sets)
        tag = int(line_addr // self.num_sets)
        return set_idx, tag

    def _make_observation(self):
        # build sliding window of (delta,op) pairs; delta is normalized address delta
        start = max(0, self.ptr - self.window_size + 1)
        window = self.trace[start:self.ptr + 1]
        # pad left if necessary
        pad = self.window_size - len(window)
        obs = []
        prev_addr = None
        for _ in range(pad):
            obs.extend([0.0, 0.0])
        for entry in window:
            addr = entry["addr"]
            if prev_addr is None:
                delta = 0.0
            else:
                delta = float((addr - prev_addr) // self.block_size)
            # normalize delta with small scale
            delta_norm = delta / (delta + 16.0)
            obs.extend([delta_norm, float(entry["op"])])
            prev_addr = addr
        import numpy as _np
        return _np.asarray(obs, dtype=_np.float32)

    def reset(self):
        self.ptr = 0
        self.cache = [list() for _ in range(self.num_sets)]
        self.reuse_samplers = [ReuseSampler(window=max(64, self.window_size)) for _ in range(self.num_sets)]
        return self._make_observation()

    def get_current_info(self):
        """Return info about the upcoming access so an agent can choose an action.

        Returns a tuple (is_miss, candidate_features, set_idx). If no eviction
        candidate is required (e.g., empty slot) candidate_features will be None.
        """
        if self.ptr >= len(self.trace):
            return False, None, None
        entry = self.trace[self.ptr]
        set_idx, tag = self._addr_to_set_tag(entry["addr"])
        bucket = self.cache[set_idx]
        # check if present
        for e in bucket:
            if e["tag"] == tag:
                return False, None, set_idx
        # miss
        if len(bucket) < self.assoc:
            # will insert without eviction
            return True, None, set_idx
        # construct candidate features as in step()
        ages = [max(0, (entry["tick"] - e["last_touch"])) for e in bucket]
        freqs = [float(e["freq"]) for e in bucket]
        reuse_bins = []
        for e in bucket:
            e_line = e.get("line_addr", (e["tag"] * self.num_sets))
            repr_addr = int(e_line * self.block_size)
            dist = self.reuse_samplers[set_idx].distance(repr_addr)
            reuse_bins.append(reuse_distance_bin(dist, bins=self.reuse_bins))
        max_age = max(1.0, max(ages))
        max_freq = max(1.0, max(freqs))
        candidate_feats = []
        for a, f, rb in zip(ages, freqs, reuse_bins):
            candidate_feats.append([a / max_age, f / max_freq, float(rb)])
        return True, candidate_feats, set_idx

    def step(self, action=None):
        """Advance one trace access. `action` may be None when not evicting.

        Returns: obs, reward, done, info
        """
        if self.ptr >= len(self.trace):
            return None, 0.0, True, {}

        entry = self.trace[self.ptr]
        set_idx, tag = self._addr_to_set_tag(entry["addr"])
        # update reuse sampler with raw address
        self.reuse_samplers[set_idx].observe(entry["addr"])

        # search for tag in set
        bucket = self.cache[set_idx]
        hit = False
        for e in bucket:
            if e["tag"] == tag:
                hit = True
                # update metadata
                e["last_touch"] = entry["tick"]
                e["freq"] += 1
                break

        reward = 0.0
        info = {"hit": hit}

        if hit:
            reward = self.hit_reward
        else:
            # miss: need to insert; if there is empty slot, insert without eviction
            if len(bucket) < self.assoc:
                bucket.append({"tag": tag, "last_touch": entry["tick"], "freq": 1, "line_addr": line_addr})
                reward = -self.dram_penalty
            else:
                # construct candidate features for each entry in bucket
                ages = [max(0, (entry["tick"] - e["last_touch"])) for e in bucket]
                freqs = [float(e["freq"]) for e in bucket]
                reuse_bins = []
                for e in bucket:
                    e_line = e.get("line_addr", (e["tag"] * self.num_sets))
                    repr_addr = int(e_line * self.block_size)
                    dist = self.reuse_samplers[set_idx].distance(repr_addr)
                    reuse_bins.append(reuse_distance_bin(dist, bins=self.reuse_bins))
                # candidate features: [age_norm, freq_norm, reuse_bin]
                max_age = max(1.0, max(ages))
                max_freq = max(1.0, max(freqs))
                candidate_feats = []
                for a, f, rb in zip(ages, freqs, reuse_bins):
                    candidate_feats.append([a / max_age, f / max_freq, float(rb)])

                # choose victim: prefer agent action if provided, else default LRU
                victim_idx = None
                if action is None:
                    # default LRU: pick oldest last_touch
                    oldest = 0
                    oldest_tick = bucket[0]["last_touch"]
                    for i, e in enumerate(bucket):
                        if e["last_touch"] < oldest_tick:
                            oldest_tick = e["last_touch"]
                            oldest = i
                    victim_idx = oldest
                else:
                    # interpret action
                    if isinstance(action, int) and action >= 0 and action < len(bucket):
                        victim_idx = int(action)
                    elif action == TraceEnv.ACTION_LRU:
                        # LRU
                        oldest = 0
                        oldest_tick = bucket[0]["last_touch"]
                        for i, e in enumerate(bucket):
                            if e["last_touch"] < oldest_tick:
                                oldest_tick = e["last_touch"]
                                oldest = i
                        victim_idx = oldest
                    elif action == TraceEnv.ACTION_MRU:
                        # MRU: most recently used
                        m = 0
                        m_tick = bucket[0]["last_touch"]
                        for i, e in enumerate(bucket):
                            if e["last_touch"] > m_tick:
                                m_tick = e["last_touch"]
                                m = i
                        victim_idx = m
                    else:
                        # unknown action: fallback to random
                        import random
                        victim_idx = random.randrange(len(bucket))

                evicted = bucket[victim_idx]
                evicted_tag = evicted["tag"]
                # perform eviction: store representative line_addr for reuse checks
                bucket[victim_idx] = {"tag": tag, "last_touch": entry["tick"], "freq": 1, "line_addr": line_addr}

                # compute lookahead: was evicted_tag accessed within `history` steps ahead?
                reused = False
                for j in range(1, min(self.history, len(self.trace) - self.ptr)):
                    future = self.trace[self.ptr + j]
                    f_set, f_tag = self._addr_to_set_tag(future["addr"])
                    if f_tag == evicted_tag:
                        reused = True
                        break

                # reward: miss penalty plus extra penalty if eviction caused reuse
                reward = -self.dram_penalty
                if reused:
                    reward -= self.dram_penalty  # extra punishment

        # advance pointer and return next observation
        self.ptr += 1
        done = (self.ptr >= len(self.trace))
        obs = self._make_observation()
        return obs, float(reward), done, info

