#include "intellicore/cache_agent.hpp"

#include <cassert>

int main() {
    intellicore::CacheAgent agent{0};
    const intellicore::MemoryAccess access{
        .cycle = 1,
        .core_id = 0,
        .address = 0x1000,
        .is_write = false,
        .cache_level = intellicore::CacheLevel::L2,
    };

    const auto decision = agent.observe(access);

    assert(agent.core_id() == 0);
    assert(decision.prefetch_address.has_value());
    assert(decision.prefetch_address.value() == 0x1040);
    return 0;
}
