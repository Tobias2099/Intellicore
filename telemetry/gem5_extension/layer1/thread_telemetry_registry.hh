#ifndef __INTELLICORE_LAYER1_THREAD_TELEMETRY_REGISTRY_HH__
#define __INTELLICORE_LAYER1_THREAD_TELEMETRY_REGISTRY_HH__

#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>

#include "layer1/telemetry_types.hh"
#include "layer1/telemetry_config.hh"
#include "layer1/thread_telemetry_state.hh"

namespace gem5
{
namespace intellicore
{

class ThreadTelemetryRegistry
{
  public:
    static constexpr std::size_t MaxThreadCount =
        static_cast<std::size_t>(std::numeric_limits<ThreadId>::max()) + 1;

    explicit ThreadTelemetryRegistry(
        uint32_t bufferCapacity = DefaultThreadBufferCapacity,
        CoreId defaultCoreId = 0);

    ThreadTelemetryState &getOrCreateState(ThreadId threadId);

    ThreadTelemetryState *tryGetState(ThreadId threadId);
    const ThreadTelemetryState *tryGetState(ThreadId threadId) const;

    void migrate(ThreadId threadId, CoreId newCoreId);

    std::size_t size() const;

  private:
    using StateSlot = std::optional<ThreadTelemetryState>;

    std::array<StateSlot, MaxThreadCount> states;
    const uint32_t bufferCapacity;
    const CoreId defaultCoreId;
    std::size_t stateCount;
};

} // namespace intellicore
} // namespace gem5

#endif // __INTELLICORE_LAYER1_THREAD_TELEMETRY_REGISTRY_HH__
