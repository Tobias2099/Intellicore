from intellicore_control.models import CacheConfig, Gem5RunConfig, MemoryConfig, TelemetryConfig
from intellicore_control.planner import build_run_plan


def test_run_plan_is_deterministic() -> None:
    config = Gem5RunConfig(
        name="baseline",
        isa="x86",
        cores=4,
        clock="3GHz",
        memory=MemoryConfig(type="DDR4", size="8GiB"),
        caches={"l2": CacheConfig(size="256KiB", associativity=8, policy="lru")},
        telemetry=TelemetryConfig(metrics=["ipc", "mpki"], deterministic_seed=42),
    )

    first = build_run_plan(config)
    second = build_run_plan(config)

    assert first == second
    assert first.run_id.startswith("run-")
