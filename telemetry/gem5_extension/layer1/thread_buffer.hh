#ifndef __INTELLICORE_LAYER1_THREAD_BUFFER_HH__
#define __INTELLICORE_LAYER1_THREAD_BUFFER_HH__

#include <atomic>
#include <cstdint>
#include <optional>
#include <vector>

#include "layer1/telemetry_config.hh"
#include "layer1/telemetry_record.hh"

namespace gem5
{
  namespace intellicore
  {

    class ThreadBuffer
    {
    public:
      explicit ThreadBuffer(
          uint32_t capacity = DefaultThreadBufferCapacity)
          : slots(capacity + 1), head(0), tail(0), droppedTraces(0), capacity_(capacity + 1)
      {
      }

      bool tryPush(const TelemetryRecord &record)
      {
        const uint32_t localTail = tail.load(std::memory_order_relaxed);
        const uint32_t nextTail = increment(localTail);
        const uint32_t localHead = head.load(std::memory_order_acquire);

        if (nextTail == localHead)
        {
          droppedTraces.fetch_add(1, std::memory_order_relaxed);
          return false;
        }

        slots[localTail] = record;
        tail.store(nextTail, std::memory_order_release);
        return true;
      }

      std::optional<TelemetryRecord> tryPop()
      {
        const uint32_t localHead = head.load(std::memory_order_relaxed);
        const uint32_t localTail = tail.load(std::memory_order_acquire);
        if (localHead == localTail)
        {
          return std::nullopt;
        }

        TelemetryRecord record = slots[localHead];
        head.store(increment(localHead), std::memory_order_release);
        return record;
      }

      uint32_t size() const
      {
        const uint32_t localHead = head.load(std::memory_order_acquire);
        const uint32_t localTail = tail.load(std::memory_order_acquire);
        if (localTail >= localHead)
        {
          return localTail - localHead;
        }
        return (capacity_ - localHead) + localTail;
      }

      uint32_t freeSlots() const
      {
        return capacity_ - size() - 1;
      }

      uint64_t droppedCount() const
      {
        return droppedTraces.load(std::memory_order_relaxed);
      }

      uint32_t capacity() const
      {
        return capacity_;
      }

    private:
      uint32_t increment(uint32_t idx) const
      {
        return (idx + 1) % capacity_;
      }

      std::vector<TelemetryRecord> slots;
      std::atomic<uint32_t> head;
      std::atomic<uint32_t> tail;
      std::atomic<uint64_t> droppedTraces;
      uint32_t capacity_;
    };

  } // namespace intellicore
} // namespace gem5

#endif // __INTELLICORE_LAYER1_THREAD_BUFFER_HH__
