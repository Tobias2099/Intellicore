from m5.objects.Gem5TelemetryProbe import Gem5TelemetryProbe
from m5.objects.X86CPU import X86TimingSimpleCPU
from m5.params import Param


class X86TelemetryTimingSimpleCPU(X86TimingSimpleCPU):
    type = "X86TelemetryTimingSimpleCPU"
    cxx_header = "layer1/telemetry_timing_simple_cpu.hh"
    cxx_class = "gem5::intellicore::TelemetryTimingSimpleCPU"

    telemetry_probe = Param.Gem5TelemetryProbe(
        "Telemetry probe that owns per-thread migration state"
    )
