#include "layer1/thread_telemetry_registry.hh"

#include "params/ThreadTelemetryRegistry.hh"

namespace gem5
{
namespace intellicore
{

ThreadTelemetryRegistry::ThreadTelemetryRegistry(
    const ThreadTelemetryRegistryParams &p)
    : SimObject(p),
      states(),
      bufferCapacity(p.buffer_capacity),
      stateCount(0),
      registryMutex()
{
}

ThreadTelemetryState &
ThreadTelemetryRegistry::getOrCreateState(
    ThreadId threadId, CoreId initialCoreId)
{
    std::lock_guard<std::mutex> lock(registryMutex);
    StateSlot &slot = states[threadId];
    if (!slot.has_value()) {
        slot.emplace(threadId, initialCoreId, bufferCapacity);
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
        slot.emplace(threadId, newCoreId, bufferCapacity);
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

bool
ThreadTelemetryRegistry::tryPopRecord(
    ThreadId threadId, TelemetryRecord &outRecord)
{
    ThreadTelemetryState *const state = tryGetState(threadId);
    if (state == nullptr) {
        return false;
    }

    auto value = state->buffer().tryPop();
    if (!value.has_value()) {
        return false;
    }

    outRecord = *value;
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
