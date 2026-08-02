#include "layer1/thread_telemetry_state.hh"

namespace gem5
{
namespace intellicore
{

ThreadTelemetryState::ThreadTelemetryState(
    ThreadId _threadId,
    CoreId _coreId,
    uint32_t bufferCapacity)
    : threadId(_threadId),
      coreId(_coreId),
      buffer_(bufferCapacity)
{
}

bool
ThreadTelemetryState::append(const TelemetryRecord &record)
{
    return buffer_.tryPush(record);
}

void
ThreadTelemetryState::updateCore(CoreId newCoreId)
{
    coreId = newCoreId;
}

ThreadBuffer &
ThreadTelemetryState::buffer()
{
    return buffer_;
}

const ThreadBuffer &
ThreadTelemetryState::buffer() const
{
    return buffer_;
}

} // namespace intellicore
} // namespace gem5
