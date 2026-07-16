#ifndef __INTELLICORE_GEM5_EXTENSION_PROBE_SMOKE_HH__
#define __INTELLICORE_GEM5_EXTENSION_PROBE_SMOKE_HH__

#include "mem/probes/base.hh"
#include "sim/stats.hh"

namespace gem5
{

struct IntellicoreProbeSmokeParams;

class IntellicoreProbeSmoke : public BaseMemProbe
{
  public:
    IntellicoreProbeSmoke(const IntellicoreProbeSmokeParams &params);

  protected:
    void handleRequest(const probing::PacketInfo &pkt_info) override;

  private:
    struct IntellicoreProbeSmokeStats : public statistics::Group
    {
        IntellicoreProbeSmokeStats(IntellicoreProbeSmoke *parent);

        statistics::Scalar events;
    } stats;
};

} // namespace gem5

#endif // __INTELLICORE_GEM5_EXTENSION_PROBE_SMOKE_HH__
