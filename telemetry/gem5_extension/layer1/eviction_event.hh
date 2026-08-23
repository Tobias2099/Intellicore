#ifndef __INTELLICORE_LAYER1_EVICTION_EVENT_HH__
#define __INTELLICORE_LAYER1_EVICTION_EVENT_HH__

#include <array>
#include <cstdint>

#include "base/types.hh"
#include "mem/request.hh"

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
    Addr address = 0;
    RequestorID requestorId = Request::invldRequestorId;

    bool isHit = false;
    bool isEviction = false;
    uint8_t evictionWayIndex = 0;
    std::array<EvictionLineData, 8> lines{};
    bool isSecure = false;

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
    buildLineDataVector(const std::array<EvictionLineData, 8> &lineData)
    {
        std::array<uint8_t, 8> fields{};
        for (std::size_t way = 0; way < fields.size(); ++way) {
            fields[way] = packLineData(lineData[way]);
        }
        return fields;
    }
};

} // namespace intellicore
} // namespace gem5

#endif // __INTELLICORE_LAYER1_EVICTION_EVENT_HH__
