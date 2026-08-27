from m5.SimObject import SimObject
from m5.objects.telemetry_config import DEFAULT_THREAD_BUFFER_CAPACITY
from m5.params import Param


class ThreadTelemetryRegistry(SimObject):
    type = "ThreadTelemetryRegistry"
    cxx_header = "layer1/thread_telemetry_registry.hh"
    cxx_class = "gem5::intellicore::ThreadTelemetryRegistry"

    buffer_capacity = Param.Unsigned(
        DEFAULT_THREAD_BUFFER_CAPACITY,
        "Usable records in each shared per-thread telemetry ring buffer",
    )
