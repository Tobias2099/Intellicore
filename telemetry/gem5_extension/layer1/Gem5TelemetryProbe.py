from m5.SimObject import SimObject
from m5.params import *
from m5.proxy import Parent
from telemetry_config import DEFAULT_THREAD_BUFFER_CAPACITY


class Gem5TelemetryProbe(SimObject):
    type = "Gem5TelemetryProbe"
    cxx_header = "layer1/gem5_telemetry_probe.hh"
    cxx_class = "gem5::intellicore::Gem5TelemetryProbe"

    manager = VectorParam.SimObject(
        Parent.any, "Cache probe manager(s) to instrument"
    )
    hit_probe_name = Param.String("Hit", "Cache hit probe point")
    miss_probe_name = Param.String("Miss", "Cache miss probe point")
    core_id = Param.UInt8(0, "Core that owns this telemetry probe")

    thread_buffer_capacity = Param.Unsigned(
        DEFAULT_THREAD_BUFFER_CAPACITY, "Per-probe ring buffer capacity"
    )
