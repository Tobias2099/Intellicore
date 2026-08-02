#include "layer1/gem5_telemetry_probe.hh"

#include "params/Gem5TelemetryProbe.hh"

namespace gem5
{
namespace intellicore
{

Gem5TelemetryProbe::Gem5TelemetryProbe(const Gem5TelemetryProbeParams &p)
    : SimObject(p),
      stats(this),
      recordFactory(),
      registry(p.thread_buffer_capacity, p.core_id),
      hitProbeName(p.hit_probe_name),
      missProbeName(p.miss_probe_name),
      accessListeners()
{
}

Gem5TelemetryProbe::Gem5TelemetryProbeStats::Gem5TelemetryProbeStats(
    Gem5TelemetryProbe *parent)
    : statistics::Group(parent),
      ADD_STAT(traceRecords, statistics::units::Count::get(),
               "Number of MemoryTrace records emitted"),
      ADD_STAT(evictionRecords, statistics::units::Count::get(),
               "Number of EvictionSnapshot records emitted"),
      ADD_STAT(migrationRecords, statistics::units::Count::get(),
               "Number of thread migration records emitted"),
      ADD_STAT(droppedRecords, statistics::units::Count::get(),
               "Number of records dropped due to full thread buffers")
{
}

void
Gem5TelemetryProbe::AccessListener::notify(const CacheAccessProbeArg &arg)
{
    parent.handleAccess(arg, isHit);
}

void
Gem5TelemetryProbe::regProbeListeners()
{
    const auto &p = dynamic_cast<const Gem5TelemetryProbeParams &>(params());
    accessListeners.reserve(p.manager.size() * 2);
    for (int i = 0; i < p.manager.size(); ++i) {
        ProbeManager *const mgr(p.manager[i]->getProbeManager());
        accessListeners.push_back(
            mgr->connect<AccessListener>(*this, hitProbeName, true));
        accessListeners.push_back(
            mgr->connect<AccessListener>(*this, missProbeName, false));
    }
}

void
Gem5TelemetryProbe::handleAccess(const CacheAccessProbeArg &arg, bool isHit)
{
    probing::PacketInfo pktInfo(arg.pkt);
    const ThreadId threadId = threadIdFor(arg.pkt);
    pktInfo.id = threadId;

    const auto record = recordFactory.buildTraceRecord(
        pktInfo, isHit, false, 0);

    if (!registry.getOrCreateState(threadId).append(record)) {
        stats.droppedRecords++;
        return;
    }

    stats.traceRecords++;
}

bool
Gem5TelemetryProbe::recordEviction(const EvictionEvent &event)
{
    const ThreadId threadId = static_cast<ThreadId>(event.requestorId & 0xFFu);
    const auto record = recordFactory.buildEvictionRecord(event);
    if (!registry.getOrCreateState(threadId).append(record)) {
        stats.droppedRecords++;
        return false;
    }

    stats.evictionRecords++;
    return true;
}

bool
Gem5TelemetryProbe::recordMigration(
    ThreadId threadId,
    CoreId newCoreId,
    uint64_t markerAddress)
{
    ThreadTelemetryState &state = registry.getOrCreateState(threadId);
    const auto record = recordFactory.buildMigrationRecord(
        threadId, newCoreId, markerAddress);
    const bool appended = state.append(record);
    registry.migrate(threadId, newCoreId);

    if (!appended) {
        stats.droppedRecords++;
        return false;
    }

    stats.migrationRecords++;
    return true;
}

bool
Gem5TelemetryProbe::tryPopRecord(
    ThreadId threadId,
    TelemetryRecord &outRecord)
{
    ThreadTelemetryState *const state = registry.tryGetState(threadId);
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

ThreadTelemetryRegistry &
Gem5TelemetryProbe::telemetryRegistry()
{
    return registry;
}

const ThreadTelemetryRegistry &
Gem5TelemetryProbe::telemetryRegistry() const
{
    return registry;
}

ThreadId
Gem5TelemetryProbe::threadIdFor(const PacketPtr &pkt)
{
    if (pkt->req->hasContextId()) {
        return static_cast<ThreadId>(pkt->req->contextId() & 0xFFu);
    }
    return static_cast<ThreadId>(pkt->req->requestorId() & 0xFFu);
}

} // namespace intellicore
} // namespace gem5
