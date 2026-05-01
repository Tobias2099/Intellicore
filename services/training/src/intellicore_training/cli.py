from __future__ import annotations

import argparse
from pathlib import Path

from .rewards import RewardWeights


def train(config: Path) -> None:
    if not config.exists():
        raise FileNotFoundError(config)

    from .config_loader import load_config

    payload = load_config(config)
    weights = RewardWeights(**payload.get("reward_weights", {}))
    print(f"Loaded {payload['name']} for {payload['target_cache_level']} with rewards={weights}")
    print("Training loop placeholder ready for trace replay integration.")


def app() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate IntelliCore cache agents.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    train_parser = subparsers.add_parser("train")
    train_parser.add_argument("--config", required=True, type=Path)

    args = parser.parse_args()
    if args.command == "train":
        train(args.config)


if __name__ == "__main__":
    app()
