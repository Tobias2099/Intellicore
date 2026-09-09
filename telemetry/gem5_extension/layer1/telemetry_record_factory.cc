#include "layer1/telemetry_record_factory.hh"

namespace gem5
{
namespace intellicore
{

std::atomic<uint64_t> TelemetryRecordFactory::recordCounter{0};

uint32_t
TelemetryRecordFactory::allocateRecordId()
{
    const uint64_t next = recordCounter.fetch_add(1, std::memory_order_relaxed);
    return static_cast<uint32_t>(next & 0xFFFFFFFFu);
}

uint8_t
TelemetryRecordFactory::classifyMemoryEvent(const probing::PacketInfo &pktInfo)
{
    if (pktInfo.cmd.isRead()) {
        return static_cast<uint8_t>(MemoryEventKind::Read);
    }
    if (pktInfo.cmd.isWrite()) {
        return static_cast<uint8_t>(MemoryEventKind::Write);
    }
    return static_cast<uint8_t>(MemoryEventKind::Other);
}

TelemetryRecord
TelemetryRecordFactory::buildTraceRecord(
    const probing::PacketInfo &pktInfo,
    bool isHit,
    bool isEviction,
    uint8_t evictionWayIndex) const
{
    TelemetryRecord record;
    record.setKind(RecordKind::MemoryTrace);
    record.setIsHit(isHit);
    record.setIsEviction(isEviction);
    record.setEvictedWayIndex(isEviction ?
        (evictionWayIndex & TelemetryRecord::EvictedWayMask) : 0);
    record.recordCounter = allocateRecordId();

    MemoryTracePayload payload;
    payload.threadId = static_cast<uint8_t>(pktInfo.id & 0xFFu);
    payload.opType = classifyMemoryEvent(pktInfo);
    payload.address = pktInfo.addr;
    payload.coherenceMap = static_cast<uint8_t>(pktInfo.flags & 0xFFu);
    record.setMemoryTracePayload(payload);

    return record;
}

TelemetryRecord
TelemetryRecordFactory::buildEvictionRecord(
    const EvictionEvent &event,
    uint32_t correlatedRecordCounter) const
{
    TelemetryRecord record;
    record.setKind(RecordKind::EvictionSnapshot);
    record.setIsHit(event.isHit);
    record.setIsEviction(event.isEviction);
    record.setEvictedWayIndex(event.evictionWayIndex);
    record.recordCounter = correlatedRecordCounter;

    EvictionSnapshotPayload payload;
    payload.fields = EvictionEvent::buildLineDataVector(event.lines);
    record.setEvictionSnapshotPayload(payload);

    return record;
}

TelemetryRecord
TelemetryRecordFactory::buildMigrationRecord(
    uint8_t threadId,
    uint8_t newCoreId,
    uint64_t markerAddress) const
{
    TelemetryRecord record;
    record.setKind(RecordKind::MemoryTrace);
    record.setIsHit(false);
    record.setIsEviction(false);
    record.setEvictedWayIndex(0);
    record.recordCounter = allocateRecordId();

    MemoryTracePayload payload;
    payload.threadId = threadId;
    payload.opType = static_cast<uint8_t>(MemoryEventKind::Migration);
    payload.address = markerAddress;
    payload.coherenceMap = newCoreId;
    record.setMemoryTracePayload(payload);

    return record;
}

} // namespace intellicore
} // namespace gem5
