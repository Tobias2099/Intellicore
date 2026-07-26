from m5.objects.BaseMemProbe import BaseMemProbe
from m5.params import *


class Gem5TelemetryProbe(BaseMemProbe):
    type = "Gem5TelemetryProbe"
    cxx_header = "gem5_telemetry_probe.hh"
    cxx_class = "gem5::intellicore::Gem5TelemetryProbe"

    # Typical values are "Hit", "Miss", or "PktRequest".
    probe_name = Param.String("PktRequest", "Primary packet probe name")

    # BaseCache registers this hook as "Data Update".
    data_update_probe_name = Param.String(
        "Data Update", "Probe used to observe cache data invalidations"
    )

    thread_buffer_capacity = Param.Unsigned(
        65536, "Per-probe ring buffer capacity"
    )