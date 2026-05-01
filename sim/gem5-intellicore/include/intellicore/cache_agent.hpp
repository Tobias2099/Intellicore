#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace intellicore {

enum class CacheLevel {
    L1I,
    L1D,
    L2,
    LLC,
};

struct MemoryAccess {
    std::uint64_t cycle;
    std::uint32_t core_id;
    std::uint64_t address;
    bool is_write;
    CacheLevel cache_level;
};

struct AgentDecision {
    std::optional<std::uint64_t> prefetch_address;
    double survival_score;
    std::string coordination_hint;
};

class CacheAgent {
  public:
    explicit CacheAgent(std::uint32_t core_id);

    [[nodiscard]] std::uint32_t core_id() const;
    [[nodiscard]] AgentDecision observe(const MemoryAccess& access) const;

  private:
    std::uint32_t core_id_;
};

}  // namespace intellicore
