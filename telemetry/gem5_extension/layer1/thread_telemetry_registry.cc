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
      stateCount(0),
      registryMutex()
{
}

ThreadTelemetryState &
ThreadTelemetryRegistry::getOrCreateState(ThreadId threadId)
{
    std::lock_guard<std::mutex> lock(registryMutex);
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
    std::lock_guard<std::mutex> lock(registryMutex);
    StateSlot &slot = states[threadId];
    return slot.has_value() ? &*slot : nullptr;
}

const ThreadTelemetryState *
ThreadTelemetryRegistry::tryGetState(ThreadId threadId) const
{
    std::lock_guard<std::mutex> lock(registryMutex);
    const StateSlot &slot = states[threadId];
    return slot.has_value() ? &*slot : nullptr;
}

void
ThreadTelemetryRegistry::migrate(ThreadId threadId, CoreId newCoreId)
{
    std::lock_guard<std::mutex> lock(registryMutex);
    StateSlot &slot = states[threadId];
    if (!slot.has_value()) {
        slot.emplace(threadId, defaultCoreId, bufferCapacity);
        ++stateCount;
    }
    slot->updateCore(newCoreId);
}

std::optional<CoreId>
ThreadTelemetryRegistry::coreIdFor(ThreadId threadId) const
{
    std::lock_guard<std::mutex> lock(registryMutex);
    const StateSlot &slot = states[threadId];
    if (!slot.has_value()) {
        return std::nullopt;
    }
    return slot->coreId;
}

bool
ThreadTelemetryRegistry::migrateIfCurrent(
    ThreadId threadId,
    CoreId expectedCoreId,
    CoreId newCoreId)
{
    std::lock_guard<std::mutex> lock(registryMutex);
    StateSlot &slot = states[threadId];
    if (!slot.has_value() || slot->coreId != expectedCoreId ||
        expectedCoreId == newCoreId) {
        return false;
    }
    slot->updateCore(newCoreId);
    return true;
}

std::size_t
ThreadTelemetryRegistry::size() const
{
    std::lock_guard<std::mutex> lock(registryMutex);
    return stateCount;
}

} // namespace intellicore
} // namespace gem5
