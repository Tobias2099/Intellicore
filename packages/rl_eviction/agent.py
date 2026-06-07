"""Lightweight RL agent for cache eviction decisions.

This module implements `RLEvictionAgent`, a self-contained, lightweight
reinforcement-learning agent intended to be evaluated inline with cache
eviction logic. It supports two modes:

- ``tabular``: simple discretized Q-table keyed by (state, action) tuples.
- ``nn``: a tiny NumPy MLP (`TinyMLP`) used as a function approximator.

The agent expects compact state and per-candidate feature vectors. For
PARSEC-like CPU workloads the features may include PC-hash buckets,
coarse reuse-distance bins, and an EWMA miss-rate value. The implementation
is intentionally minimal to keep evaluation latency small.

Design goals:
- Minimal dependencies (NumPy-only runtime).
- Small memory footprint for Q-table or tiny NN weights.
- Clear, easy-to-integrate APIs: `select_action`, `update`, `save`, `load`.
"""
from typing import Sequence, Optional, Tuple, List
import numpy as np
import pickle

from .config import DEFAULT_CONFIG
from .models import TinyMLP


def _bin(value: float, bins: int) -> int:
    """Discretize a normalized value in [0,1] into `bins` buckets.

    Inputs are assumed to be in [0,1]. Values outside that range will
    be clipped to the valid bucket range.
    """
    if bins <= 1:
        return 0
    idx = int(np.floor(value * bins))
    return max(0, min(bins - 1, idx))


class RLEvictionAgent:
    """Reinforcement-learning eviction agent.

    Parameters
    - config: optional dict to override `DEFAULT_CONFIG` values.

    The agent stores configuration in `self.cfg` and exposes basic hyper-
    parameters as attributes for quick tuning. In tabular mode a Python
    dictionary `self.q` holds Q-values keyed by `(state_key, action_key)`.
    In NN mode `self.model` is an instance of `TinyMLP` used to estimate
    action values for given (state, action) inputs.
    """

    def __init__(self, config: Optional[dict] = None):
        cfg = dict(DEFAULT_CONFIG)
        if config:
            cfg.update(config)
        self.cfg = cfg
        np.random.seed(cfg.get("seed", 0))

        # core RL hyperparameters
        self.mode = cfg.get("mode", "tabular")
        self.alpha = cfg.get("alpha", 0.1)
        self.gamma = cfg.get("gamma", 0.99)
        # epsilon for exploration (epsilon-greedy)
        self.epsilon = cfg.get("epsilon", 0.1)
        self.min_epsilon = cfg.get("min_epsilon", 0.01)
        self.epsilon_decay = cfg.get("epsilon_decay", 1.0)

        # discretization bins for basic features
        self.age_bins = cfg.get("age_bins", 8)
        self.freq_bins = cfg.get("freq_bins", 8)

        # reward shaping for cache events
        self.hit_reward = cfg.get("hit_reward", 1.0)
        self.dram_penalty = cfg.get("dram_penalty", 1.0)

        # workload-aware flags and params (PC hashing, reuse sampling, EWMA)
        self.use_pc = cfg.get("use_pc", True)
        self.pc_buckets = int(cfg.get("pc_buckets", 64))
        self.use_reuse = cfg.get("use_reuse", True)
        self.reuse_bins = int(cfg.get("reuse_bins", 5))
        self.use_ewma_miss = cfg.get("use_ewma_miss", True)

        # storage: tabular Q-table or tiny NN model
        self.q = {} if self.mode == "tabular" else None
        self.model = None
        if self.mode == "nn":
            input_dim = int(cfg.get("nn_input_dim", 7))
            self.model = TinyMLP(input_dim, hidden=cfg.get("nn_hidden", 32), lr=cfg.get("alpha", 1e-3), seed=cfg.get("seed", 0))

    def _state_key(self, state: Sequence[float]) -> Tuple:
        """Build a discrete key for the (possibly continuous) state.

        The simplest state is [avg_age, avg_freq]. If EWMA miss-rate is
        provided it is treated as a third element and discretized as well.
        The returned tuple is suitable for use as a dict key in the
        tabular Q-table.
        """
        a = _bin(state[0], self.age_bins)
        f = _bin(state[1], self.freq_bins)
        if len(state) > 2:
            ew = _bin(state[2], max(2, self.freq_bins))
            return (int(a), int(f), int(ew))
        return (int(a), int(f))

    def _action_key(self, action_feat: Sequence[float]) -> Tuple:
        """Build a discrete key for an action (candidate line).

        The action features typically begin with normalized `age` and
        `freq`. Additional compact integer features such as `pc_bucket`
        and `reuse_bin` may follow; include them verbatim in the key so
        the tabular agent can learn per-bucket values.
        """
        a = _bin(action_feat[0], self.age_bins)
        f = _bin(action_feat[1], self.freq_bins)
        if len(action_feat) > 2:
            pc = int(action_feat[2])
            rb = int(action_feat[3]) if len(action_feat) > 3 else 0
            return (int(a), int(f), int(pc), int(rb))
        return (int(a), int(f))

    def _pad_input(self, inp: List[float]) -> List[float]:
        """Pad or truncate an input vector to the model's expected dimension.

        The tiny NN has a fixed input width; callers may provide fewer or
        more features so we pad with zeros or truncate to keep dimensions
        consistent. This is a pragmatic choice to avoid reinitializing the
        NN for small feature set changes.
        """
        if self.model is None:
            return inp
        dim = self.model.w1.shape[0]
        if len(inp) < dim:
            return inp + [0.0] * (dim - len(inp))
        return inp[:dim]

    def select_action(self, state: Sequence[float], candidate_features: Sequence[Sequence[float]]) -> int:
        """Choose which candidate (cache line) to evict.

        The agent supports epsilon-greedy exploration. In tabular mode the
        agent looks up Q-values from `self.q` for each candidate; in NN
        mode it evaluates the tiny MLP on a concatenation of state and
        candidate features. The method returns the selected candidate
        index (integer).
        """
        if len(candidate_features) == 0:
            raise ValueError("no candidates provided")

        # TABULAR MODE: use discretized keys and a simple epsilon-greedy policy
        if self.mode == "tabular":
            s_key = self._state_key(state)
            if np.random.rand() < self.epsilon:
                # explore uniformly
                return int(np.random.randint(len(candidate_features)))
            qs = [self.q.get((s_key, self._action_key(c)), 0.0) for c in candidate_features]
            return int(int(np.argmax(qs)))

        # NN MODE: evaluate the TinyMLP on (state || candidate) inputs
        vals = []
        for c in candidate_features:
            inp = list(state) + list(c)
            inp = self._pad_input(inp)
            vals.append(self.model.predict(inp))
        if np.random.rand() < self.epsilon:
            return int(np.random.randint(len(candidate_features)))
        return int(int(np.argmax(vals)))

    def update(self, state: Sequence[float], action_idx: int, reward: float, next_state: Sequence[float], next_candidate_features: Sequence[Sequence[float]]):
        """Apply an online learning update from a transition.

        The transition is (state, action_idx, reward, next_state, next_candidates).
        - In tabular mode we apply the standard Q-learning update to the
          stored `self.q[(state_key, action_key)]` entry.
        - In NN mode we form a target value (reward + gamma * max_next)
          and perform a single SGD update on the TinyMLP toward that
          target for the chosen (state, action) input.

        This is an online, sample-by-sample update suitable for running in
        a cache loop where each access yields a single learning step.
        """
        if self.mode == "tabular":
            s_key = self._state_key(state)
            a_feat = next_candidate_features[action_idx] if action_idx < len(next_candidate_features) else [0.0, 0.0]
            a_key = self._action_key(a_feat)
            key = (s_key, a_key)
            cur_q = self.q.get(key, 0.0)

            # estimate best next value over available next-candidates
            max_next = 0.0
            if next_candidate_features:
                next_keys = [self.q.get((self._state_key(next_state), self._action_key(c)), 0.0) for c in next_candidate_features]
                max_next = max(next_keys)

            # Q-learning update (one-step)
            new_q = cur_q + self.alpha * (reward + self.gamma * max_next - cur_q)
            self.q[key] = float(new_q)
        else:
            # NN: compute target and perform a single gradient step toward it
            max_next = 0.0
            if next_candidate_features:
                vals = []
                for c in next_candidate_features:
                    inp = list(next_state) + list(c)
                    inp = self._pad_input(inp)
                    vals.append(self.model.predict(inp))
                max_next = max(vals)
            target = reward + self.gamma * max_next

            action_feat = (next_candidate_features[action_idx] if action_idx < len(next_candidate_features) else [0.0, 0.0])
            inp = list(state) + list(action_feat)
            inp = self._pad_input(inp)
            self.model.sgd_update(inp, target)

        # decay epsilon gradually but do not go below min_epsilon
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

    def reward_from_access(self, hit: bool) -> float:
        return self.hit_reward if hit else -self.dram_penalty

    def save(self, path: str):
        data = {"cfg": self.cfg, "mode": self.mode}
        if self.mode == "tabular":
            data["q"] = self.q
        else:
            data["model"] = {"w1": self.model.w1, "b1": self.model.b1, "w2": self.model.w2, "b2": self.model.b2}
        with open(path, "wb") as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path: str) -> "RLEvictionAgent":
        with open(path, "rb") as f:
            data = pickle.load(f)
        agent = cls(data.get("cfg"))
        if data.get("mode") == "tabular":
            agent.q = data.get("q", {})
        else:
            m = data.get("model", {})
            if agent.model and m:
                agent.model.w1 = m.get("w1")
                agent.model.b1 = m.get("b1")
                agent.model.w2 = m.get("w2")
                agent.model.b2 = m.get("b2")
        return agent
