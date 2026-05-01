from __future__ import annotations

from hashlib import sha256

from .models import Gem5RunConfig, RunPlan


def build_run_plan(config: Gem5RunConfig) -> RunPlan:
    """Create a deterministic run plan identifier from simulator-critical inputs."""
    fingerprint = sha256(
        f"{config.name}:{config.isa}:{config.cores}:{config.telemetry.deterministic_seed}".encode(
            "utf-8"
        )
    ).hexdigest()[:12]

    return RunPlan(
        run_id=f"run-{fingerprint}",
        config_name=config.name,
        isa=config.isa,
        cores=config.cores,
        metrics=config.telemetry.metrics,
        deterministic_seed=config.telemetry.deterministic_seed,
    )
