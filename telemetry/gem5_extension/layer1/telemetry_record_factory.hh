#ifndef __INTELLICORE_LAYER1_TELEMETRY_RECORD_FACTORY_HH__
#define __INTELLICORE_LAYER1_TELEMETRY_RECORD_FACTORY_HH__

#include <atomic>
#include <cstdint>

#include "layer1/eviction_event.hh"
#include "layer1/telemetry_record.hh"
#include "sim/probe/mem.hh"

namespace gem5
{
namespace intellicore
{

class TelemetryRecordFactory
{
  public:
    TelemetryRecord buildTraceRecord(
        const probing::PacketInfo &pktInfo,
        bool isHit,
        bool isEviction,
        uint8_t evictionWayIndex) const;

    TelemetryRecord buildEvictionRecord(const EvictionEvent &event) const;

    TelemetryRecord buildMigrationRecord(
        uint8_t threadId,
        uint8_t newCoreId,
        uint64_t markerAddress = 0) const;

  private:
    static uint32_t allocateRecordId();
    static uint8_t classifyMemoryEvent(const probing::PacketInfo &pktInfo);

    static std::atomic<uint64_t> recordCounter;
};

} // namespace intellicore
} // namespace gem5

#endif // __INTELLICORE_LAYER1_TELEMETRY_RECORD_FACTORY_HH__