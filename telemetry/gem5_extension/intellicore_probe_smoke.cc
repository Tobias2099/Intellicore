#include "intellicore_probe_smoke.hh"

#include "params/IntellicoreProbeSmoke.hh"

namespace gem5
{

IntellicoreProbeSmoke::IntellicoreProbeSmoke(
        const IntellicoreProbeSmokeParams &p)
    : BaseMemProbe(p),
      stats(this)
{
}

IntellicoreProbeSmoke::IntellicoreProbeSmokeStats::
IntellicoreProbeSmokeStats(IntellicoreProbeSmoke *parent)
    : statistics::Group(parent),
      ADD_STAT(events, statistics::units::Count::get(),
               "Number of memory probe callbacks received")
{
}

void
IntellicoreProbeSmoke::handleRequest(const probing::PacketInfo &pkt_info)
{
    (void)pkt_info;
    stats.events++;
}

} // namespace gem5
