"""Tiny NumPy MLP used as an optional function approximator."""
from typing import Sequence
import numpy as np


class TinyMLP:
    """Very small MLP with one hidden layer and SGD updates.

    Designed to be dependency-free (only numpy) and fast enough for
    low-latency evaluation next to cache eviction policies.
    """

    def __init__(self, input_dim: int, hidden: int = 32, lr: float = 1e-3, seed: int = 0):
        rng = np.random.RandomState(seed)
        self.w1 = rng.randn(input_dim, hidden).astype(np.float32) * (1.0 / np.sqrt(input_dim))
        self.b1 = np.zeros(hidden, dtype=np.float32)
        self.w2 = rng.randn(hidden, 1).astype(np.float32) * (1.0 / np.sqrt(hidden))
        self.b2 = np.zeros(1, dtype=np.float32)
        self.lr = float(lr)

    def forward(self, x: np.ndarray) -> np.ndarray:
        h = np.tanh(x @ self.w1 + self.b1)
        out = h @ self.w2 + self.b2
        return out.reshape(-1)

    def predict(self, x: Sequence[float]) -> float:
        x = np.asarray(x, dtype=np.float32).reshape(1, -1)
        return float(self.forward(x)[0])

    def sgd_update(self, x: Sequence[float], target: float):
        x = np.asarray(x, dtype=np.float32).reshape(1, -1)
        # forward
        h = np.tanh(x @ self.w1 + self.b1)
        out = h @ self.w2 + self.b2  # shape (1,1)
        error = (out.reshape(-1)[0] - float(target))
        # gradients (MSE)
        d_out = 2.0 * error
        gw2 = (h.T * d_out)
        gb2 = d_out
        dh = (self.w2.reshape(1, -1) * d_out) * (1 - h * h)
        gw1 = x.T @ dh
        gb1 = dh.reshape(-1)
        # apply
        self.w2 -= self.lr * gw2
        self.b2 -= self.lr * gb2
        self.w1 -= self.lr * gw1
        self.b1 -= self.lr * gb1
