#ifndef __INTELLICORE_LAYER1_EVICTION_EVENT_HH__
#define __INTELLICORE_LAYER1_EVICTION_EVENT_HH__

#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>

#include "mem/cache/cache_probe_arg.hh"
#include "sim/probe/mem.hh"

namespace gem5
{
namespace intellicore
{

struct EvictionLineData
{
    uint8_t saturationCounter = 0;
    uint8_t lruRank = 0;
    bool dirtyBit = false;
    bool invalidBit = false;
    bool accessBit = false;
};

class EvictionEvent
{
  public:
    static constexpr uint8_t UnknownWay = 0x7;

    Addr address = 0;
    RequestorID requestorId = Request::invldRequestorId;

    bool isHit = false;
    bool isEviction = false;
    uint8_t evictionWayIndex = UnknownWay;
    EvictionLineData line;

    static bool packetLooksLikeEviction(const probing::PacketInfo &pkt)
    {
        return pkt.cmd.isEviction() ||
               pkt.cmd == MemCmd::WritebackDirty ||
               pkt.cmd == MemCmd::WritebackClean ||
               pkt.cmd == MemCmd::CleanEvict;
    }

    static std::optional<EvictionEvent>
    fromDataUpdateHook(const CacheDataUpdateProbeArg &arg)
    {
        if (!arg.newData.empty()) {
            return std::nullopt;
        }

        EvictionEvent event;
        event.address = arg.addr;
        event.requestorId = arg.requestorID;
        event.isEviction = true;
        event.evictionWayIndex = UnknownWay;

        return event;
    }

    static uint8_t packLineData(const EvictionLineData &lineData)
    {
        uint8_t packed = 0;
        packed |= (lineData.saturationCounter & 0x3u);
        packed |= ((lineData.lruRank & 0x7u) << 2);
        packed |= (lineData.dirtyBit ? 1u : 0u) << 5;
        packed |= (lineData.invalidBit ? 1u : 0u) << 6;
        packed |= (lineData.accessBit ? 1u : 0u) << 7;
        return packed;
    }

    static std::array<uint8_t, 8>
    buildLineDataVector(const EvictionLineData &lineData)
    {
        std::array<uint8_t, 8> fields{};
        fields[0] = packLineData(lineData);
        return fields;
    }

    void setSaturationFromRefCount(uint64_t refCount)
    {
        line.saturationCounter = static_cast<uint8_t>(
            std::min<uint64_t>(refCount, 0x3u));
    }
};

} // namespace intellicore
} // namespace gem5

#endif // __INTELLICORE_LAYER1_EVICTION_EVENT_HH__