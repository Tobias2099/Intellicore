#include "intellicore/cache_agent.hpp"

namespace intellicore {

CacheAgent::CacheAgent(std::uint32_t core_id) : core_id_(core_id) {}

std::uint32_t CacheAgent::core_id() const {
    return core_id_;
}

AgentDecision CacheAgent::observe(const MemoryAccess& access) const {
    AgentDecision decision{};
    decision.survival_score = access.is_write ? 0.65 : 0.75;

    if (!access.is_write) {
        decision.prefetch_address = access.address + 64;
    }

    decision.coordination_hint = "local-observation";
    return decision;
}

}  // namespace intellicore
