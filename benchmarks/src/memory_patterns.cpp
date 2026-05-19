#include <algorithm>
#include <chrono>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
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
  vector<int> arr(n, 1);
  volatile size_t sum = 0;

  vector<size_t> idx;
  if (mode == Mode::RANDOM)
  {
    idx.resize(n);
    iota(idx.begin(), idx.end(), 0);
    std::mt19937 rng(0); // default seed is set to 0 for reproducibility
    shuffle(idx.begin(), idx.end(), rng);
  }

  auto timeStart = chrono::high_resolution_clock::now();

  switch (mode)
  {
  case Mode::SEQUENTIAL:
    for (size_t i = 0; i < n; i++)
    {
      sum += arr[i];
    }
    break;

  case Mode::RANDOM:
    for (size_t i = 0; i < n; i++)
    {
      sum += arr[idx[i]];
    }
    break;

  case Mode::STRIDE:
  {
    const size_t stride = 16;
    // sum all elements using stride accesses
    for (size_t offset = 0; offset < stride; offset++)
    {
      for (size_t i = offset; i < n; i += stride)
      {
        sum += arr[i];
      }
    }
    break;
  }

  case Mode::HOTCOLD:
  {
    const size_t cache_line_ints = 16; // 64-byte cache line / 4-byte int
    const size_t rounds = 256;
    const size_t hot_n = min(n, static_cast<size_t>(16 * 1024));      // 64 KiB
    const size_t max_cold_n = static_cast<size_t>(32 * 1024);         // 128 KiB
    const size_t cold_n = n > hot_n ? min(n - hot_n, max_cold_n) : 0;

    for (size_t round = 0; round < rounds; round++)
    {
      for (size_t i = 0; i < hot_n; i++)
      {
        sum += arr[i];
      }

      for (size_t i = hot_n; i < hot_n + cold_n; i += cache_line_ints)
      {
        sum += arr[i];
      }

      for (size_t i = 0; i < hot_n; i++)
      {
        sum += arr[i];
      }
    }
    break;
  }
  }

  auto timeEnd = chrono::high_resolution_clock::now();
  auto duration = chrono::duration_cast<chrono::milliseconds>(timeEnd - timeStart).count();

  cout << "Mode: " << modeName(mode) << ", Time: " << duration << " ms, Sum: " << sum << endl;
}
