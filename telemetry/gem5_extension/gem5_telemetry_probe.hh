#ifndef __INTELLICORE_GEM5_EXTENSION_TELEMETRY_PROBE_HH__
#define __INTELLICORE_GEM5_EXTENSION_TELEMETRY_PROBE_HH__

#include <cstdint>
#include <unordered_map>
#include <vector>

#include "layer1/telemetry_record_factory.hh"
#include "layer1/thread_buffer.hh"
#include "mem/cache/cache_probe_arg.hh"
#include "mem/probes/base.hh"
#include "sim/stats.hh"

namespace gem5
{

struct Gem5TelemetryProbeParams;

namespace intellicore
{

class Gem5TelemetryProbe : public BaseMemProbe
{
  public:
    Gem5TelemetryProbe(const Gem5TelemetryProbeParams &params);

    void regProbeListeners() override;

    bool tryPopRecord(TelemetryRecord &outRecord);

  protected:
    void handleRequest(const probing::PacketInfo &pktInfo) override;

  private:
    struct DataUpdateListener : public ProbeListenerArgBase<CacheDataUpdateProbeArg>
    {
        DataUpdateListener(Gem5TelemetryProbe &_parent, std::string name)
            : ProbeListenerArgBase(std::move(name)), parent(_parent)
        {}

        void notify(const CacheDataUpdateProbeArg &arg) override;

        Gem5TelemetryProbe &parent;
    };

    struct AccessHint
    {
        bool sawAccess = false;
        bool isHit = false;
        bool likelyDirty = false;
        uint64_t refs = 0;
    };

    struct Gem5TelemetryProbeStats : public statistics::Group
    {
        Gem5TelemetryProbeStats(Gem5TelemetryProbe *parent);

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

#endif // __INTELLICORE_GEM5_EXTENSION_TELEMETRY_PROBE_HH__