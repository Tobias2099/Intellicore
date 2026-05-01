from __future__ import annotations

import json
import argparse
from pathlib import Path

from .models import Gem5RunConfig
from .planner import build_run_plan


def plan_run(config: Path) -> None:
    """Validate a gem5 config and print a deterministic run plan."""
    if not config.exists():
        raise FileNotFoundError(config)

    run_config = Gem5RunConfig.from_yaml(config)
    plan = build_run_plan(run_config)
    print(json.dumps(plan.model_dump(), indent=2))


def app() -> None:
    parser = argparse.ArgumentParser(description="IntelliCore simulation control plane.")
    subparsers = parser.add_subparsers(dest="resource", required=True)
    runs = subparsers.add_parser("runs", help="Plan and manage gem5 simulation runs.")
    run_commands = runs.add_subparsers(dest="command", required=True)
    plan = run_commands.add_parser("plan", help="Validate a gem5 config and print a run plan.")
    plan.add_argument("--config", required=True, type=Path)

    args = parser.parse_args()
    if args.resource == "runs" and args.command == "plan":
        plan_run(args.config)


if __name__ == "__main__":
    app()
