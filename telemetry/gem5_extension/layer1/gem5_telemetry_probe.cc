#include "layer1/gem5_telemetry_probe.hh"

#include <algorithm>
#include <array>
#include <cstddef>
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
      fillProbeName(p.fill_probe_name),
      replacementProbeName(p.replacement_probe_name),
      cacheLineSize(p.cache_line_size),
      listeners(),
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
               "Number of records dropped due to full thread buffers"),
      ADD_STAT(unattributedReplacements, statistics::units::Count::get(),
               "Replacement events without a linked demand-miss trace"),
      ADD_STAT(malformedReplacementSnapshots,
               statistics::units::Count::get(),
               "Replacement events with malformed set, way, or LRU metadata")
{
}

void
Gem5TelemetryProbe::AccessListener::notify(const CacheAccessProbeArg &arg)
{
    parent.handleAccess(arg, isHit);
}

void
Gem5TelemetryProbe::FillListener::notify(const CacheAccessProbeArg &arg)
{
    parent.handleFill(arg);
}

void
Gem5TelemetryProbe::ReplacementListener::notify(
    const CacheReplacementProbeArg &arg)
{
    parent.handleReplacement(arg);
}

void
Gem5TelemetryProbe::regProbeListeners()
{
    const auto &p = dynamic_cast<const Gem5TelemetryProbeParams &>(params());
    listeners.reserve(p.manager.size() * 4);
    for (int i = 0; i < p.manager.size(); ++i) {
        ProbeManager *const mgr(p.manager[i]->getProbeManager());
        listeners.push_back(
            mgr->connect<AccessListener>(*this, hitProbeName, true));
        listeners.push_back(
            mgr->connect<AccessListener>(*this, missProbeName, false));
        listeners.push_back(
            mgr->connect<FillListener>(*this, fillProbeName));
        listeners.push_back(
            mgr->connect<ReplacementListener>(*this, replacementProbeName));
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

    if (!isHit && isDemandMiss(arg.pkt)) {
        auto extension = arg.pkt->req->getExtension<TraceLinkExtension>();
        if (!extension) {
            extension = std::make_shared<TraceLinkExtension>();
            arg.pkt->req->setExtension(extension);
        }
        extension->set(this, TraceLink{record.recordCounter, threadId});
    }
}

bool
Gem5TelemetryProbe::recordEviction(
    const EvictionEvent &event,
    ThreadId threadId,
    uint32_t correlatedRecordCounter)
{
    const auto record = recordFactory.buildEvictionRecord(
        event, correlatedRecordCounter);
    if (!registry.getOrCreateState(threadId).append(record)) {
        stats.droppedRecords++;
        return false;
    }

    stats.evictionRecords++;
    return true;
}

void
Gem5TelemetryProbe::handleReplacement(const CacheReplacementProbeArg &arg)
{
    if (arg.cause != CacheReplacementCause::Allocation ||
        arg.triggerPkt == nullptr || arg.triggerPkt->req == nullptr) {
        stats.unattributedReplacements++;
        return;
    }

    auto extension =
        arg.triggerPkt->req->getExtension<TraceLinkExtension>();
    const TraceLink *const link = extension ? extension->find(this) : nullptr;
    if (link == nullptr) {
        stats.unattributedReplacements++;
        return;
    }

    const TraceLink trace_link = *link;
    if (arg.lines.size() != 8 || arg.victimWay >= 8 ||
        arg.lines[arg.victimWay].way != arg.victimWay ||
        !arg.lines[arg.victimWay].valid) {
        stats.malformedReplacementSnapshots++;
        clearTraceLink(arg.triggerPkt->req);
        return;
    }

    const std::size_t valid_lines = std::count_if(
        arg.lines.begin(), arg.lines.end(),
        [](const CacheReplacementLineInfo &line) { return line.valid; });
    std::array<bool, 8> ways_seen{};
    std::array<bool, 8> ranks_seen{};
    for (const auto &line : arg.lines) {
        if (line.way >= ways_seen.size() || ways_seen[line.way] ||
            (line.valid &&
             (line.lruRank >= valid_lines || ranks_seen[line.lruRank]))) {
            stats.malformedReplacementSnapshots++;
            clearTraceLink(arg.triggerPkt->req);
            return;
        }
        ways_seen[line.way] = true;
        if (line.valid) {
            ranks_seen[line.lruRank] = true;
        }
    }

    EvictionEvent event;
    event.address = arg.lines[arg.victimWay].addr;
    event.requestorId = arg.triggerPkt->req->requestorId();
    event.isHit = false;
    event.isEviction = true;
    event.evictionWayIndex = arg.victimWay;
    event.isSecure = arg.lines[arg.victimWay].isSecure;

    for (const auto &source : arg.lines) {
        panic_if(source.way >= event.lines.size(),
                 "Replacement snapshot contains an out-of-range way");
        auto &destination = event.lines[source.way];
        destination.lruRank = source.lruRank;
        destination.dirtyBit = source.dirty;
        destination.invalidBit = !source.valid;
        if (source.valid) {
            destination.saturationCounter = saturationCounterFor(
                arg.cache, source.addr, source.isSecure);
        }
    }

    recordEviction(
        event, trace_link.threadId, trace_link.recordCounter);

    clearTraceLink(arg.triggerPkt->req);
}

void
Gem5TelemetryProbe::handleFill(const CacheAccessProbeArg &arg)
{
    clearTraceLink(arg.pkt->req);
}

void
Gem5TelemetryProbe::clearTraceLink(const RequestPtr &request)
{
    auto extension = request->getExtension<TraceLinkExtension>();
    if (!extension) {
        return;
    }
    extension->erase(this);
    if (extension->empty()) {
        request->removeExtension<TraceLinkExtension>();
    }
}

bool
Gem5TelemetryProbe::isDemandMiss(const PacketPtr &pkt) const
{
    return pkt->isDemand();
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
