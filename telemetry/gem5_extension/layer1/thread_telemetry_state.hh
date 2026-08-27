#ifndef __INTELLICORE_LAYER1_THREAD_TELEMETRY_STATE_HH__
#define __INTELLICORE_LAYER1_THREAD_TELEMETRY_STATE_HH__

#include <cstdint>

#include "layer1/telemetry_record.hh"
#include "layer1/telemetry_config.hh"
#include "layer1/telemetry_types.hh"
#include "layer1/thread_buffer.hh"

namespace gem5
{
namespace intellicore
{

class ThreadTelemetryRegistry;

class ThreadTelemetryState
{
  public:
    ThreadTelemetryState(
        ThreadId threadId,
        CoreId coreId,
        uint32_t bufferCapacity = DefaultThreadBufferCapacity);

    bool append(const TelemetryRecord &record);

    void updateCore(CoreId newCoreId);

    ThreadBuffer &buffer();
    const ThreadBuffer &buffer() const;

    const ThreadId threadId;

  private:
    friend class ThreadTelemetryRegistry;

    CoreId coreId;
    ThreadBuffer buffer_;
};

} // namespace intellicore
} // namespace gem5

#endif // __INTELLICORE_LAYER1_THREAD_TELEMETRY_STATE_HH__
