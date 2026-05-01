from intellicore_control.telemetry import TelemetryEvent


def test_telemetry_event_requires_non_negative_cycle() -> None:
    event = TelemetryEvent(run_id="run-1", cycle=0, core_id=0, metric="ipc", value=1.2)

    assert event.metric == "ipc"
    assert event.tags == {}
