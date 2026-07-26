#include "gem5_telemetry_probe.hh"

#include "params/BaseMemProbe.hh"
#include "params/Gem5TelemetryProbe.hh"

namespace gem5
{
namespace intellicore
{

Gem5TelemetryProbe::Gem5TelemetryProbe(const Gem5TelemetryProbeParams &p)
    : BaseMemProbe(p),
      stats(this),
      recordFactory(),
      buffer(p.thread_buffer_capacity),
      dataUpdateProbeName(p.data_update_probe_name),
      dataUpdateListeners(),
      accessHints()
{
}

Gem5TelemetryProbe::Gem5TelemetryProbeStats::Gem5TelemetryProbeStats(
    Gem5TelemetryProbe *parent)
    : statistics::Group(parent),
      ADD_STAT(traceRecords, statistics::units::Count::get(),
               "Number of MemoryTrace records emitted"),
      ADD_STAT(evictionRecords, statistics::units::Count::get(),
               "Number of EvictionSnapshot records emitted"),
      ADD_STAT(droppedRecords, statistics::units::Count::get(),
               "Number of records dropped due to full thread buffer")
{
}

void
Gem5TelemetryProbe::DataUpdateListener::notify(const CacheDataUpdateProbeArg &arg)
{
    parent.handleDataUpdate(arg);
}

bool
Gem5TelemetryProbe::inferHitFromProbeName() const
{
    const auto &p = dynamic_cast<const Gem5TelemetryProbeParams &>(params());
    return p.probe_name == "Hit";
}

void
Gem5TelemetryProbe::regProbeListeners()
{
    BaseMemProbe::regProbeListeners();

    const auto &p = dynamic_cast<const Gem5TelemetryProbeParams &>(params());
    dataUpdateListeners.reserve(p.manager.size());
    for (int i = 0; i < p.manager.size(); ++i) {
        ProbeManager *const mgr(p.manager[i]->getProbeManager());
        dataUpdateListeners.push_back(
            mgr->connect<DataUpdateListener>(*this, dataUpdateProbeName));
    }
}

void
Gem5TelemetryProbe::handleRequest(const probing::PacketInfo &pktInfo)
{
    const bool isHit = inferHitFromProbeName();
    const bool isEviction = EvictionEvent::packetLooksLikeEviction(pktInfo);

    auto &hint = accessHints[pktInfo.addr];
    hint.sawAccess = true;
    hint.isHit = isHit;
    hint.refs++;
    if (pktInfo.cmd == MemCmd::WritebackDirty || pktInfo.cmd.isWrite()) {
        hint.likelyDirty = true;
    }

    const auto record = recordFactory.buildTraceRecord(
        pktInfo,
        isHit,
        isEviction,
        isEviction ? TelemetryRecord::UnknownWay : 0);

    if (!buffer.tryPush(record)) {
        stats.droppedRecords++;
        return;
    }

    stats.traceRecords++;
}

void
Gem5TelemetryProbe::handleDataUpdate(const CacheDataUpdateProbeArg &arg)
{
    auto eventOpt = EvictionEvent::fromDataUpdateHook(arg);
    if (!eventOpt.has_value()) {
        return;
    }

    EvictionEvent event = *eventOpt;

    const auto found = accessHints.find(arg.addr);
    if (found != accessHints.end()) {
        const AccessHint &hint = found->second;
        event.isHit = hint.isHit;
        event.line.accessBit = hint.sawAccess;
        event.line.dirtyBit = hint.likelyDirty;
        event.setSaturationFromRefCount(hint.refs);
    }

    // Generic probe hooks expose block address and data transition, but not
    // replacement way/LRU order for the victim. We keep these fields as
    // explicit unknown defaults until a cache-specific hook is provided.
    event.evictionWayIndex = EvictionEvent::UnknownWay;
    event.line.lruRank = 0x7;
    event.line.invalidBit = false;

    recordEviction(event);
}

void
Gem5TelemetryProbe::recordEviction(const EvictionEvent &event)
{
    const auto record = recordFactory.buildEvictionRecord(event);
    if (!buffer.tryPush(record)) {
        stats.droppedRecords++;
        return;
    }

    stats.evictionRecords++;
}

bool
Gem5TelemetryProbe::tryPopRecord(TelemetryRecord &outRecord)
{
    auto value = buffer.tryPop();
    if (!value.has_value()) {
        return false;
    }

    outRecord = *value;
    return true;
}

} // namespace intellicore
} // namespace gem5