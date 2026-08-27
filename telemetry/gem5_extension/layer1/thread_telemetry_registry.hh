#ifndef __INTELLICORE_LAYER1_THREAD_TELEMETRY_REGISTRY_HH__
#define __INTELLICORE_LAYER1_THREAD_TELEMETRY_REGISTRY_HH__

#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <mutex>
#include <optional>

#include "layer1/telemetry_types.hh"
#include "layer1/telemetry_config.hh"
#include "layer1/thread_telemetry_state.hh"
#include "sim/sim_object.hh"

namespace gem5
{

struct ThreadTelemetryRegistryParams;

namespace intellicore
{

class ThreadTelemetryRegistry : public SimObject
{
  public:
    static constexpr std::size_t MaxThreadCount =
        static_cast<std::size_t>(std::numeric_limits<ThreadId>::max()) + 1;

    explicit ThreadTelemetryRegistry(
        const ThreadTelemetryRegistryParams &params);

    ThreadTelemetryState &getOrCreateState(
        ThreadId threadId, CoreId initialCoreId);

    ThreadTelemetryState *tryGetState(ThreadId threadId);
    const ThreadTelemetryState *tryGetState(ThreadId threadId) const;

    void migrate(ThreadId threadId, CoreId newCoreId);

    std::optional<CoreId> coreIdFor(ThreadId threadId) const;

    bool migrateIfCurrent(
        ThreadId threadId,
        CoreId expectedCoreId,
        CoreId newCoreId);

    bool tryPopRecord(ThreadId threadId, TelemetryRecord &outRecord);

    std::size_t size() const;

  private:
    using StateSlot = std::optional<ThreadTelemetryState>;

    std::array<StateSlot, MaxThreadCount> states;
    const uint32_t bufferCapacity;
    std::size_t stateCount;
    mutable std::mutex registryMutex;
};

} // namespace intellicore
} // namespace gem5

#endif // __INTELLICORE_LAYER1_THREAD_TELEMETRY_REGISTRY_HH__
