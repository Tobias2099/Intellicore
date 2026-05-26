#include <algorithm>
#include <chrono>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <thread>
#include <vector>

using namespace std;

enum class Mode
{
  SEQUENTIAL,
  RANDOM,
  STRIDE,
  HOTCOLD,
};

const char *modeName(Mode mode)
{
  switch (mode)
  {
  case Mode::SEQUENTIAL:
    return "Sequential";
  case Mode::RANDOM:
    return "Random";
  case Mode::STRIDE:
    return "Stride";
  case Mode::HOTCOLD:
    return "HotCold";
  }

  return "Unknown";
}

int main(int argc, char **argv)
{
  Mode mode = Mode::SEQUENTIAL; // default mode

  if (argc > 1)
  {
    string mode_str(argv[1]);
    if (mode_str == "sequential")
      mode = Mode::SEQUENTIAL;
    else if (mode_str == "random")
      mode = Mode::RANDOM;
    else if (mode_str == "stride")
      mode = Mode::STRIDE;
    else if (mode_str == "hotcold")
      mode = Mode::HOTCOLD;
    else
    {
      cerr << "Unknown mode: " << mode_str << endl;
      return 1;
    }
  }

  const size_t n = argc > 2 ? std::stoull(argv[2]) : 64 * 1024 * 1024;
  const size_t thread_count = argc > 3 ? max<size_t>(1, std::stoull(argv[3])) : 1;
  vector<int> arr(n, 1);
  vector<size_t> partial_sums(thread_count, 0);

  vector<size_t> idx;
  if (mode == Mode::RANDOM)
  {
    idx.resize(n);
    iota(idx.begin(), idx.end(), 0);
    std::mt19937 rng(0); // default seed is set to 0 for reproducibility
    shuffle(idx.begin(), idx.end(), rng);
  }

  auto timeStart = chrono::high_resolution_clock::now();

  auto range_begin = [n, thread_count](size_t thread_id) {
    return (n * thread_id) / thread_count;
  };
  auto range_end = [n, thread_count](size_t thread_id) {
    return (n * (thread_id + 1)) / thread_count;
  };

  auto worker = [&](size_t thread_id) {
    size_t local_sum = 0;

    switch (mode)
    {
    case Mode::SEQUENTIAL:
      for (size_t i = range_begin(thread_id); i < range_end(thread_id); i++)
      {
        local_sum += arr[i];
      }
      break;

    case Mode::RANDOM:
      for (size_t i = range_begin(thread_id); i < range_end(thread_id); i++)
      {
        local_sum += arr[idx[i]];
      }
      break;

    case Mode::STRIDE:
    {
      const size_t stride = 16;
      for (size_t offset = thread_id; offset < stride; offset += thread_count)
      {
        for (size_t i = offset; i < n; i += stride)
        {
          local_sum += arr[i];
        }
      }
      break;
    }

    case Mode::HOTCOLD:
    {
      const size_t cache_line_ints = 16; // 64-byte cache line / 4-byte int
      const size_t rounds = 256;
      const size_t hot_n = min(n, static_cast<size_t>(16 * 1024)); // 64 KiB
      const size_t max_cold_n = static_cast<size_t>(32 * 1024);    // 128 KiB
      const size_t cold_n = n > hot_n ? min(n - hot_n, max_cold_n) : 0;

      const size_t hot_begin = (hot_n * thread_id) / thread_count;
      const size_t hot_end = (hot_n * (thread_id + 1)) / thread_count;
      const size_t cold_begin = hot_n + (cold_n * thread_id) / thread_count;
      const size_t cold_end = hot_n + (cold_n * (thread_id + 1)) / thread_count;

      for (size_t round = 0; round < rounds; round++)
      {
        for (size_t i = hot_begin; i < hot_end; i++)
        {
          local_sum += arr[i];
        }

        for (size_t i = cold_begin; i < cold_end; i += cache_line_ints)
        {
          local_sum += arr[i];
        }

        for (size_t i = hot_begin; i < hot_end; i++)
        {
          local_sum += arr[i];
        }
      }
      break;
    }
    }

    partial_sums[thread_id] = local_sum;
  };

  vector<thread> workers;
  workers.reserve(thread_count);
  for (size_t thread_id = 0; thread_id < thread_count; thread_id++)
  {
    workers.emplace_back(worker, thread_id);
  }

  for (thread &worker_thread : workers)
  {
    worker_thread.join();
  }

  volatile size_t sum = accumulate(partial_sums.begin(), partial_sums.end(), size_t{0});

  auto timeEnd = chrono::high_resolution_clock::now();
  auto duration = chrono::duration_cast<chrono::milliseconds>(timeEnd - timeStart).count();

  cout << "Mode: " << modeName(mode) << ", Threads: " << thread_count
       << ", Time: " << duration << " ms, Sum: " << sum << endl;
}
