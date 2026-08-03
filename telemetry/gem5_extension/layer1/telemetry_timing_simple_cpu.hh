#ifndef __INTELLICORE_LAYER1_TELEMETRY_TIMING_SIMPLE_CPU_HH__
#define __INTELLICORE_LAYER1_TELEMETRY_TIMING_SIMPLE_CPU_HH__

#include "cpu/simple/timing.hh"
#include "params/X86TelemetryTimingSimpleCPU.hh"

namespace gem5
{
namespace intellicore
{

class Gem5TelemetryProbe;

class TelemetryTimingSimpleCPU : public TimingSimpleCPU
{
  public:
    PARAMS(X86TelemetryTimingSimpleCPU);

    explicit TelemetryTimingSimpleCPU(const Params &params);

    void activateContext(ThreadID threadId) override;
    void suspendContext(ThreadID threadId) override;
    void haltContext(ThreadID threadId) override;

  private:
    void observeContext(ThreadID threadId);

    Gem5TelemetryProbe *const telemetryProbe;
    bool handlingHalt = false;
};

} // namespace intellicore
} // namespace gem5

#endif // __INTELLICORE_LAYER1_TELEMETRY_TIMING_SIMPLE_CPU_HH__
