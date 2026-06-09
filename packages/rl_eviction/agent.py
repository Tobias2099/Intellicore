"""Lightweight RL agent for eviction decisions with workload-aware features.

Supports tabular Q and small NN (TinyMLP). Accepts candidate feature vectors
that may include PC buckets and reuse-distance bins. NN inputs are padded
or truncated to the configured `nn_input_dim` to keep the model fixed-size.
"""
from typing import Sequence, Optional, Tuple, List
import numpy as np
import pickle

from .config import DEFAULT_CONFIG
from .models import TinyMLP


def _bin(value: float, bins: int) -> int:
    if bins <= 1:
        return 0
    idx = int(np.floor(value * bins))
    return max(0, min(bins - 1, idx))


class RLEvictionAgent:
    def __init__(self, config: Optional[dict] = None):
        cfg = dict(DEFAULT_CONFIG)
        if config:
            cfg.update(config)
        self.cfg = cfg
        np.random.seed(cfg.get("seed", 0))
        self.mode = cfg.get("mode", "tabular")
        self.alpha = cfg.get("alpha", 0.1)
        self.gamma = cfg.get("gamma", 0.99)
        self.epsilon = cfg.get("epsilon", 0.1)
        self.min_epsilon = cfg.get("min_epsilon", 0.01)
        self.epsilon_decay = cfg.get("epsilon_decay", 1.0)
        self.age_bins = cfg.get("age_bins", 8)
        self.freq_bins = cfg.get("freq_bins", 8)
        self.hit_reward = cfg.get("hit_reward", 1.0)
        self.dram_penalty = cfg.get("dram_penalty", 1.0)

        # workload-aware features
        self.use_pc = cfg.get("use_pc", True)
        self.pc_buckets = int(cfg.get("pc_buckets", 64))
        self.use_reuse = cfg.get("use_reuse", True)
        self.reuse_bins = int(cfg.get("reuse_bins", 5))
        self.use_ewma_miss = cfg.get("use_ewma_miss", True)

        self.q = {} if self.mode == "tabular" else None
        self.model = None
        if self.mode == "nn":
            input_dim = int(cfg.get("nn_input_dim", 7))
            self.model = TinyMLP(input_dim, hidden=cfg.get("nn_hidden", 32), lr=cfg.get("alpha", 1e-3), seed=cfg.get("seed", 0))

    def _state_key(self, state: Sequence[float]) -> Tuple:
        # discretize state which may include ewma miss as third element
        a = _bin(state[0], self.age_bins)
        f = _bin(state[1], self.freq_bins)
        if len(state) > 2:
            ew = _bin(state[2], max(2, self.freq_bins))
            return (int(a), int(f), int(ew))
        return (int(a), int(f))

    def _action_key(self, action_feat: Sequence[float]) -> Tuple:
        # action_feat may be [age, freq] or [age, freq, pc_bucket, reuse_bin]
        a = _bin(action_feat[0], self.age_bins)
        f = _bin(action_feat[1], self.freq_bins)
        if len(action_feat) > 2:
            pc = int(action_feat[2])
            rb = int(action_feat[3]) if len(action_feat) > 3 else 0
            return (int(a), int(f), int(pc), int(rb))
        return (int(a), int(f))

    def _pad_input(self, inp: List[float]) -> List[float]:
        if self.model is None:
            return inp
        dim = self.model.w1.shape[0]
        if len(inp) < dim:
            return inp + [0.0] * (dim - len(inp))
        return inp[:dim]

    def select_action(self, state: Sequence[float], candidate_features: Sequence[Sequence[float]]) -> int:
        """Select index of candidate to evict.

        state: [avg_age, avg_freq, (optional) ewma_miss]
        candidate_features: list of per-line features (age,freq[,pc_bucket,reuse_bin])
        """
        if len(candidate_features) == 0:
            raise ValueError("no candidates provided")
        if self.mode == "tabular":
            s_key = self._state_key(state)
            # epsilon-greedy
            if np.random.rand() < self.epsilon:
                return int(np.random.randint(len(candidate_features)))
            qs = []
            for c in candidate_features:
                a_key = self._action_key(c)
                qs.append(self.q.get((s_key, a_key), 0.0))
            return int(int(np.argmax(qs)))

        else:
            # nn mode: evaluate each candidate with concatenated features
            vals = []
            for c in candidate_features:
                inp = list(state) + list(c)
                inp = self._pad_input(inp)
                vals.append(self.model.predict(inp))
            if np.random.rand() < self.epsilon:
                return int(np.random.randint(len(candidate_features)))
            return int(int(np.argmax(vals)))

    def update(self, state: Sequence[float], action_idx: int, reward: float, next_state: Sequence[float], next_candidate_features: Sequence[Sequence[float]]):
        """Perform an online Q update (tabular) or single-step SGD (nn)."""
        if self.mode == "tabular":
            s_key = self._state_key(state)
            a_feat = next_candidate_features[action_idx] if action_idx < len(next_candidate_features) else [0.0, 0.0]
            a_key = self._action_key(a_feat)
            key = (s_key, a_key)
            cur_q = self.q.get(key, 0.0)
            # compute max next
            max_next = 0.0
            if next_candidate_features:
                next_keys = [self.q.get((self._state_key(next_state), self._action_key(c)), 0.0) for c in next_candidate_features]
                max_next = max(next_keys)
            new_q = cur_q + self.alpha * (reward + self.gamma * max_next - cur_q)
            self.q[key] = float(new_q)
        else:
            # train model toward target = reward + gamma * max_next
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

        # decay epsilon
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
