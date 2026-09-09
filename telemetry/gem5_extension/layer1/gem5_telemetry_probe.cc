#include "layer1/gem5_telemetry_probe.hh"

#include <functional>

#include "base/logging.hh"
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
      cacheLineSize(p.cache_line_size),
      accessListeners(),
      saturationCounters()
{
    fatal_if(cacheLineSize == 0 || (cacheLineSize & (cacheLineSize - 1)) != 0,
             "Gem5TelemetryProbe cache_line_size must be a power of two");
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

    // Age the line-frequency state before constructing this access record.
    // This callback is the clock for saturation updates; no CPU-cycle poller
    // participates in the update.
    updateSaturationCounter(arg);

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
    EvictionEvent enrichedEvent = event;
    if (event.cache != nullptr) {
        enrichedEvent.line.saturationCounter = saturationCounterFor(
            *event.cache, event.address, event.isSecure);
    }
    const auto record = recordFactory.buildEvictionRecord(enrichedEvent);
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
    CoreId oldCoreId,
    CoreId newCoreId,
    Tick currentTick)
{
    if (!registry.migrateIfCurrent(threadId, oldCoreId, newCoreId)) {
        return false;
    }

    ThreadTelemetryState *const state = registry.tryGetState(threadId);
    panic_if(state == nullptr,
             "Telemetry state disappeared while recording migration");
    const auto record = recordFactory.buildMigrationRecord(
        threadId, newCoreId, currentTick);
    const bool appended = state->append(record);

    if (!appended) {
        stats.droppedRecords++;
        return false;
    }

    stats.migrationRecords++;
    return true;
}

void
Gem5TelemetryProbe::observeThreadContext(
    ThreadContext &context,
    Tick currentTick)
{
    const ContextID contextId = context.contextId();
    const ThreadId threadId = static_cast<ThreadId>(
        (contextId != InvalidContextID ? contextId : context.threadId()) &
        0xFFu);
    const CoreId newCoreId = static_cast<CoreId>(context.cpuId() & 0xFFu);
    const std::optional<CoreId> oldCoreId = registry.coreIdFor(threadId);

    if (!oldCoreId.has_value()) {
        registry.migrate(threadId, newCoreId);
        return;
    }
    if (*oldCoreId != newCoreId) {
        recordMigration(threadId, *oldCoreId, newCoreId, currentTick);
    }
}

std::size_t
Gem5TelemetryProbe::LineKeyHash::operator()(const LineKey &key) const
{
    const std::size_t cacheHash =
        std::hash<const CacheAccessor *>{}(key.cache);
    const std::size_t addressHash = std::hash<Addr>{}(key.address);
    const std::size_t secureHash = std::hash<bool>{}(key.isSecure);
    return cacheHash ^ (addressHash << 1) ^ (secureHash << 2);
}

Gem5TelemetryProbe::LineKey
Gem5TelemetryProbe::lineKeyFor(
    const CacheAccessor &cache, Addr address, bool isSecure) const
{
    return LineKey{
        &cache,
        address & ~static_cast<Addr>(cacheLineSize - 1),
        isSecure
    };
}

uint8_t
Gem5TelemetryProbe::updateSaturationCounter(const CacheAccessProbeArg &arg)
{
    const LineKey accessed = lineKeyFor(
        arg.cache, arg.pkt->getAddr(), arg.pkt->isSecure());

    for (auto it = saturationCounters.begin();
         it != saturationCounters.end();) {
        if (it->first.cache == accessed.cache && !(it->first == accessed)) {
            if (it->second > 0) {
                --it->second;
            }
            if (it->second == 0) {
                it = saturationCounters.erase(it);
                continue;
            }
        }
        ++it;
    }

    uint8_t &counter = saturationCounters[accessed];
    if (counter < 3) {
        ++counter;
    }
    return counter;
}

uint8_t
Gem5TelemetryProbe::saturationCounterFor(
    const CacheAccessor &cache, Addr address, bool isSecure) const
{
    const auto found = saturationCounters.find(
        lineKeyFor(cache, address, isSecure));
    return found == saturationCounters.end() ? 0 : found->second;
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
