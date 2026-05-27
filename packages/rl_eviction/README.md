RL Eviction Policy (lightweight)
================================

This small package provides a minimal reinforcement-learning agent and
environment helpers intended to be integrated with gem5 as an eviction
policy replacement. It is intentionally lightweight (NumPy-only) and
designed for low-latency evaluation.

Quick example
-------------

```python
from rl_eviction import RLEvictionAgent, CacheEnv

env = CacheEnv(dram_penalty=1.0, hit_reward=1.0)
agent = RLEvictionAgent({"mode": "tabular"})

# Suppose we have per-line ages and freqs (float lists)
ages = [0.1, 0.5, 2.0]
freqs = [3, 1, 0]
state = env.compute_state(ages, freqs)
cands = env.compute_candidates(ages, freqs)
choice = agent.select_action(state, cands)
# After serving access, compute reward and update
hit = False
reward = env.reward(hit)
next_state = state
agent.update(state, choice, reward, next_state, cands)
```

Workload-aware features
-----------------------

This package includes lightweight encoders useful for CPU workloads (PARSEC-like):

- PC hashing (`use_pc`) to capture code-region behavior.
- Reuse-distance sampling (`ReuseSampler`) and coarse binning (`reuse_bins`).
- EWMA miss-rate (`use_ewma_miss`) to detect phases and streaming patterns.

To enable these features, pass configuration options to `RLEvictionAgent` or
use the defaults in `config.py`.

Files
-----
- `agent.py`: `RLEvictionAgent` implementation
- `env.py`: state encoders and `CacheEnv`
- `models.py`: tiny NumPy MLP used for function approximation
- `config.py`: default hyperparameters
