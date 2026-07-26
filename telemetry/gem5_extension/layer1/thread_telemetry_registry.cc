#include "layer1/thread_telemetry_registry.hh"

namespace gem5
{
namespace intellicore
{

ThreadTelemetryRegistry::ThreadTelemetryRegistry(
    uint32_t _bufferCapacity,
    CoreId _defaultCoreId)
    : states(),
      bufferCapacity(_bufferCapacity),
      defaultCoreId(_defaultCoreId),
      stateCount(0)
{
}

ThreadTelemetryState &
ThreadTelemetryRegistry::getOrCreateState(ThreadId threadId)
{
    StateSlot &slot = states[threadId];
    if (!slot.has_value()) {
        slot.emplace(threadId, defaultCoreId, bufferCapacity);
        ++stateCount;
    }
    return *slot;
}

ThreadTelemetryState *
ThreadTelemetryRegistry::tryGetState(ThreadId threadId)
{
    StateSlot &slot = states[threadId];
    return slot.has_value() ? &*slot : nullptr;
}

const ThreadTelemetryState *
ThreadTelemetryRegistry::tryGetState(ThreadId threadId) const
{
    const StateSlot &slot = states[threadId];
    return slot.has_value() ? &*slot : nullptr;
}

void
ThreadTelemetryRegistry::migrate(ThreadId threadId, CoreId newCoreId)
{
    getOrCreateState(threadId).updateCore(newCoreId);
}

std::size_t
ThreadTelemetryRegistry::size() const
{
    return stateCount;
}

} // namespace intellicore
} // namespace gem5
