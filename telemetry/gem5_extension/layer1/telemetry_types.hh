#ifndef __INTELLICORE_LAYER1_TELEMETRY_TYPES_HH__
#define __INTELLICORE_LAYER1_TELEMETRY_TYPES_HH__

#include <array>
#include <cstdint>

namespace gem5
{
namespace intellicore
{

using ThreadId = uint8_t;
using CoreId = uint8_t;

enum class RecordKind : uint8_t
{
    MemoryTrace = 0,
    EvictionSnapshot = 1
};

enum class MemoryEventKind : uint8_t
{
    Read = 0,
    Write = 1,
    Migration = 2,
    Other = 3,
};

struct MemoryTracePayload
{
    uint8_t threadId = 0;
    uint8_t opType = 0;
    uint64_t address = 0;
    uint8_t coherenceMap = 0;
};

struct EvictionSnapshotPayload
{
    std::array<uint8_t, 8> fields{};
};

} // namespace intellicore
} // namespace gem5

#endif // __INTELLICORE_LAYER1_TELEMETRY_TYPES_HH__
