#ifndef __INTELLICORE_GEM5_EXTENSION_TELEMETRY_PROBE_SMOKE_HH__
#define __INTELLICORE_GEM5_EXTENSION_TELEMETRY_PROBE_SMOKE_HH__

#include <cstdint>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "layer1/telemetry_record_factory.hh"
#include "layer1/thread_buffer.hh"
#include "mem/cache/cache_probe_arg.hh"
#include "mem/probes/base.hh"
#include "sim/stats.hh"

namespace gem5
{

struct Gem5TelemetryProbeSmokeParams;

namespace intellicore
{

class Gem5TelemetryProbeSmoke : public BaseMemProbe
{
  public:
    Gem5TelemetryProbeSmoke(const Gem5TelemetryProbeSmokeParams &params);

    void regProbeListeners() override;

    bool tryPopRecord(TelemetryRecord &outRecord);

  protected:
    void handleRequest(const probing::PacketInfo &pktInfo) override;

  private:
    struct DataUpdateListener : public ProbeListenerArgBase<CacheDataUpdateProbeArg>
    {
        DataUpdateListener(Gem5TelemetryProbeSmoke &_parent, std::string name)
            : ProbeListenerArgBase(std::move(name)), parent(_parent)
        {}

        void notify(const CacheDataUpdateProbeArg &arg) override;

        Gem5TelemetryProbeSmoke &parent;
    };

    struct AccessHint
    {
        bool sawAccess = false;
        bool isHit = false;
        bool likelyDirty = false;
        uint64_t refs = 0;
    };

    struct Gem5TelemetryProbeSmokeStats : public statistics::Group
    {
        Gem5TelemetryProbeSmokeStats(Gem5TelemetryProbeSmoke *parent);

        statistics::Scalar traceRecords;
        statistics::Scalar evictionRecords;
        statistics::Scalar droppedRecords;
    } stats;

    void handleDataUpdate(const CacheDataUpdateProbeArg &arg);
    void recordEviction(const EvictionEvent &event);

    bool inferHitFromProbeName() const;

    TelemetryRecordFactory recordFactory;
    ThreadBuffer buffer;

    const std::string dataUpdateProbeName;
    std::vector<ProbeListenerPtr<>> dataUpdateListeners;
    std::unordered_map<Addr, AccessHint> accessHints;
};

} // namespace intellicore
} // namespace gem5

#endif // __INTELLICORE_GEM5_EXTENSION_TELEMETRY_PROBE_SMOKE_HH__
