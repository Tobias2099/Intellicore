from m5.objects.BaseMemProbe import BaseMemProbe
from m5.objects.telemetry_config import DEFAULT_THREAD_BUFFER_CAPACITY
from m5.params import *


class Gem5TelemetryProbeSmoke(BaseMemProbe):
    type = "Gem5TelemetryProbeSmoke"
    cxx_header = "gem5_telemetry_probe_smoke.hh"
    cxx_class = "gem5::intellicore::Gem5TelemetryProbeSmoke"

    # Typical values are "Hit", "Miss", or "PktRequest".
    probe_name = Param.String("PktRequest", "Primary packet probe name")

    # BaseCache registers this hook as "Data Update".
    data_update_probe_name = Param.String(
        "Data Update", "Probe used to observe cache data invalidations"
    )

    thread_buffer_capacity = Param.Unsigned(
        DEFAULT_THREAD_BUFFER_CAPACITY, "Per-probe ring buffer capacity"
    )
