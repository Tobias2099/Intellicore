#include "layer1/telemetry_timing_simple_cpu.hh"

#include "layer1/gem5_telemetry_probe.hh"
#include "sim/cur_tick.hh"

namespace gem5
{
namespace intellicore
{

TelemetryTimingSimpleCPU::TelemetryTimingSimpleCPU(const Params &p)
    : TimingSimpleCPU(p), telemetryProbe(p.telemetry_probe)
{
}

void
TelemetryTimingSimpleCPU::activateContext(ThreadID threadId)
{
    TimingSimpleCPU::activateContext(threadId);
    observeContext(threadId);
}

void
TelemetryTimingSimpleCPU::suspendContext(ThreadID threadId)
{
    TimingSimpleCPU::suspendContext(threadId);
    if (!handlingHalt) {
        observeContext(threadId);
    }
}

void
TelemetryTimingSimpleCPU::haltContext(ThreadID threadId)
{
    handlingHalt = true;
    TimingSimpleCPU::haltContext(threadId);
    handlingHalt = false;
    observeContext(threadId);
}

void
TelemetryTimingSimpleCPU::observeContext(ThreadID threadId)
{
    telemetryProbe->observeThreadContext(*getContext(threadId), curTick());
}

} // namespace intellicore
} // namespace gem5
