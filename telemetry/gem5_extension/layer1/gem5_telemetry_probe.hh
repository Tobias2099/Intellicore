#ifndef __INTELLICORE_LAYER1_GEM5_TELEMETRY_PROBE_HH__
#define __INTELLICORE_LAYER1_GEM5_TELEMETRY_PROBE_HH__

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "cpu/thread_context.hh"
#include "layer1/telemetry_record_factory.hh"
#include "layer1/thread_telemetry_registry.hh"
#include "mem/cache/cache_probe_arg.hh"
#include "sim/probe/probe.hh"
#include "sim/sim_object.hh"
#include "sim/stats.hh"

namespace gem5
{

struct Gem5TelemetryProbeParams;

namespace intellicore
{

class Gem5TelemetryProbe : public SimObject
{
  public:
    Gem5TelemetryProbe(const Gem5TelemetryProbeParams &params);

    void regProbeListeners() override;

    bool tryPopRecord(ThreadId threadId, TelemetryRecord &outRecord);

    bool recordEviction(const EvictionEvent &event);

    bool recordMigration(
        ThreadId threadId,
        CoreId oldCoreId,
        CoreId newCoreId,
        Tick currentTick);

    void observeThreadContext(ThreadContext &context, Tick currentTick);

    uint8_t saturationCounterFor(
        const CacheAccessor &cache,
        Addr address,
        bool isSecure = false) const;

    ThreadTelemetryRegistry &telemetryRegistry();
    const ThreadTelemetryRegistry &telemetryRegistry() const;

  private:
    struct AccessListener : public ProbeListenerArgBase<CacheAccessProbeArg>
    {
        AccessListener(
            Gem5TelemetryProbe &_parent,
            std::string name,
            bool _isHit)
            : ProbeListenerArgBase(std::move(name)),
              parent(_parent),
              isHit(_isHit)
        {}

        void notify(const CacheAccessProbeArg &arg) override;

        Gem5TelemetryProbe &parent;
        const bool isHit;
    };

    struct Gem5TelemetryProbeStats : public statistics::Group
    {
        Gem5TelemetryProbeStats(Gem5TelemetryProbe *parent);

        statistics::Scalar traceRecords;
        statistics::Scalar evictionRecords;
        statistics::Scalar migrationRecords;
        statistics::Scalar droppedRecords;
    } stats;

    struct LineKey
    {
        const CacheAccessor *cache;
        Addr address;
        bool isSecure;

        bool operator==(const LineKey &other) const
        {
            return cache == other.cache && address == other.address &&
                   isSecure == other.isSecure;
        }
    };

    struct LineKeyHash
    {
        std::size_t operator()(const LineKey &key) const;
    };

    void handleAccess(const CacheAccessProbeArg &arg, bool isHit);
    uint8_t updateSaturationCounter(const CacheAccessProbeArg &arg);
    LineKey lineKeyFor(
        const CacheAccessor &cache, Addr address, bool isSecure) const;
    static ThreadId threadIdFor(const PacketPtr &pkt);

    TelemetryRecordFactory recordFactory;
    ThreadTelemetryRegistry registry;

    const std::string hitProbeName;
    const std::string missProbeName;
    const unsigned cacheLineSize;
    std::vector<ProbeListenerPtr<>> accessListeners;
    std::unordered_map<LineKey, uint8_t, LineKeyHash> saturationCounters;
};

} // namespace intellicore
} // namespace gem5

#endif // __INTELLICORE_LAYER1_GEM5_TELEMETRY_PROBE_HH__
