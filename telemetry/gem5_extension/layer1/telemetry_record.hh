#ifndef __INTELLICORE_LAYER1_TELEMETRY_RECORD_HH__
#define __INTELLICORE_LAYER1_TELEMETRY_RECORD_HH__

#include <array>
#include <cstddef>
#include <cstdint>

#include "layer1/telemetry_types.hh"

namespace gem5
{
namespace intellicore
{

class TelemetryRecord
{
  public:
    static constexpr uint8_t KindBit = 0;
    static constexpr uint8_t HitBit = 1;
    static constexpr uint8_t EvictionBit = 2;
    static constexpr uint8_t EvictedWayShift = 3;
    static constexpr uint8_t EvictedWayMask = 0x7;
    static constexpr uint8_t UnknownWay = 0x7;
    static constexpr std::size_t EncodedSize = 16;

    uint8_t metadata = 0;
    uint32_t recordCounter = 0;
    std::array<uint8_t, 11> payload{};

    void setKind(RecordKind kind)
    {
        if (kind == RecordKind::EvictionSnapshot) {
            metadata |= (1u << KindBit);
        } else {
            metadata &= ~(1u << KindBit);
        }
    }

    RecordKind kind() const
    {
        return (metadata & (1u << KindBit)) ?
            RecordKind::EvictionSnapshot : RecordKind::MemoryTrace;
    }

    void setIsHit(bool value)
    {
        if (value) {
            metadata |= (1u << HitBit);
        } else {
            metadata &= ~(1u << HitBit);
        }
    }

    bool isHit() const
    {
        return (metadata & (1u << HitBit)) != 0;
    }

    void setIsEviction(bool value)
    {
        if (value) {
            metadata |= (1u << EvictionBit);
        } else {
            metadata &= ~(1u << EvictionBit);
        }
    }

    bool isEviction() const
    {
        return (metadata & (1u << EvictionBit)) != 0;
    }

    void setEvictedWayIndex(uint8_t way)
    {
        metadata &= ~(EvictedWayMask << EvictedWayShift);
        metadata |= ((way & EvictedWayMask) << EvictedWayShift);
    }

    uint8_t evictedWayIndex() const
    {
        return (metadata >> EvictedWayShift) & EvictedWayMask;
    }

    void setMemoryTracePayload(const MemoryTracePayload &trace)
    {
        payload.fill(0);
        payload[0] = trace.threadId;
        payload[1] = trace.opType;
        for (std::size_t i = 0; i < sizeof(trace.address); ++i) {
            payload[2 + i] = static_cast<uint8_t>((trace.address >> (8 * i)) & 0xFFu);
        }
        payload[10] = trace.coherenceMap;
    }

    MemoryTracePayload memoryTracePayload() const
    {
        MemoryTracePayload trace;
        trace.threadId = payload[0];
        trace.opType = payload[1];
        uint64_t address = 0;
        for (std::size_t i = 0; i < sizeof(address); ++i) {
            address |= static_cast<uint64_t>(payload[2 + i]) << (8 * i);
        }
        trace.address = address;
        trace.coherenceMap = payload[10];
        return trace;
    }

    void setEvictionSnapshotPayload(const EvictionSnapshotPayload &snapshot)
    {
        payload.fill(0);
        for (std::size_t i = 0; i < snapshot.fields.size(); ++i) {
            payload[i] = snapshot.fields[i];
        }
    }

    EvictionSnapshotPayload evictionSnapshotPayload() const
    {
        EvictionSnapshotPayload snapshot;
        for (std::size_t i = 0; i < snapshot.fields.size(); ++i) {
            snapshot.fields[i] = payload[i];
        }
        return snapshot;
    }

    std::array<uint8_t, EncodedSize> encode() const
    {
        std::array<uint8_t, EncodedSize> out{};
        out[0] = metadata;
        out[1] = static_cast<uint8_t>(recordCounter & 0xFFu);
        out[2] = static_cast<uint8_t>((recordCounter >> 8) & 0xFFu);
        out[3] = static_cast<uint8_t>((recordCounter >> 16) & 0xFFu);
        out[4] = static_cast<uint8_t>((recordCounter >> 24) & 0xFFu);
        for (std::size_t i = 0; i < payload.size(); ++i) {
            out[5 + i] = payload[i];
        }
        return out;
    }
};

} // namespace intellicore
} // namespace gem5

#endif // __INTELLICORE_LAYER1_TELEMETRY_RECORD_HH__
