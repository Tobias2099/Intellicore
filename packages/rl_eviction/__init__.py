"""RL-based eviction policy package (lightweight, gem5-friendly APIs).

This package provides a minimal reinforcement-learning agent and
environment interface suitable for integrating as a cache eviction
policy within gem5 (integration not included here).
"""
from .agent import RLEvictionAgent
from .env import CacheEnv
from .config import DEFAULT_CONFIG

__all__ = ["RLEvictionAgent", "CacheEnv", "DEFAULT_CONFIG"]
