#ifndef __INTELLICORE_LAYER1_TRACE_LINK_HH__
#define __INTELLICORE_LAYER1_TRACE_LINK_HH__

#include <cstdint>
#include <memory>
#include <unordered_map>

#include "base/extensible.hh"
#include "layer1/telemetry_types.hh"
#include "mem/request.hh"

namespace gem5
{
namespace intellicore
{

class Gem5TelemetryProbe;

/** Correlation state carried by a miss Request until its fill completes. */
struct TraceLink
{
    uint32_t recordCounter = 0;
    ThreadId threadId = 0;
};

class TraceLinkExtension : public Extension<Request, TraceLinkExtension>
{
  public:
    std::unique_ptr<ExtensionBase> clone() const override
    {
        return std::make_unique<TraceLinkExtension>(*this);
    }

    void set(const Gem5TelemetryProbe *owner, const TraceLink &link)
    {
        links[owner] = link;
    }

    const TraceLink *find(const Gem5TelemetryProbe *owner) const
    {
        const auto found = links.find(owner);
        return found == links.end() ? nullptr : &found->second;
    }

    void erase(const Gem5TelemetryProbe *owner)
    {
        links.erase(owner);
    }

    bool empty() const { return links.empty(); }

  private:
    std::unordered_map<const Gem5TelemetryProbe *, TraceLink> links;
};

} // namespace intellicore
} // namespace gem5

#endif // __INTELLICORE_LAYER1_TRACE_LINK_HH__
