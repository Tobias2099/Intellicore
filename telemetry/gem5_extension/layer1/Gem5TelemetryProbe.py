from m5.SimObject import SimObject
from m5.objects.ThreadTelemetryRegistry import ThreadTelemetryRegistry
from m5.params import *
from m5.proxy import Parent


class Gem5TelemetryProbe(SimObject):
    type = "Gem5TelemetryProbe"
    cxx_header = "layer1/gem5_telemetry_probe.hh"
    cxx_class = "gem5::intellicore::Gem5TelemetryProbe"

    manager = VectorParam.SimObject(
        Parent.any, "Cache probe manager(s) to instrument"
    )
    hit_probe_name = Param.String("Hit", "Cache hit probe point")
    miss_probe_name = Param.String("Miss", "Cache miss probe point")
    fill_probe_name = Param.String("Fill", "Cache fill probe point")
    replacement_probe_name = Param.String(
        "Replacement", "True cache replacement probe point"
    )
    core_id = Param.UInt8(0, "Core that owns this telemetry probe")
    registry = Param.ThreadTelemetryRegistry(
        "System-wide registry shared by all telemetry probes"
    )
    cache_line_size = Param.Unsigned(
        Parent.cache_line_size, "Cache-line size used by saturation tracking"
    )
