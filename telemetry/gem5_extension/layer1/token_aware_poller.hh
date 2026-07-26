#ifndef __INTELLICORE_LAYER1_TOKEN_AWARE_POLLER_HH__
#define __INTELLICORE_LAYER1_TOKEN_AWARE_POLLER_HH__

#include <cstdint>
#include <vector>

#include "layer1/thread_buffer.hh"

namespace gem5
{
namespace intellicore
{

struct TraceBatch
{
    std::vector<TelemetryRecord> records;
    uint32_t drained = 0;
    uint64_t sourceDropped = 0;
};

class TokenAwarePoller
{
  public:
    TraceBatch drain(ThreadBuffer &buffer, uint32_t budget) const
    {
        TraceBatch batch;
        batch.records.reserve(budget);

        for (uint32_t i = 0; i < budget; ++i) {
            auto next = buffer.tryPop();
            if (!next.has_value()) {
                break;
            }
            batch.records.push_back(*next);
            batch.drained++;
        }

        batch.sourceDropped = buffer.droppedCount();
        return batch;
    }
};

} // namespace intellicore
} // namespace gem5

#endif // __INTELLICORE_LAYER1_TOKEN_AWARE_POLLER_HH__