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
};

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
  }

  auto timeEnd = chrono::high_resolution_clock::now();
  auto duration = chrono::duration_cast<chrono::milliseconds>(timeEnd - timeStart).count();

  cout << "Mode: " << (mode == Mode::SEQUENTIAL ? "Sequential" : mode == Mode::RANDOM ? "Random"
                                                                                      : "Stride")
       << ", Time: " << duration << " ms, Sum: " << sum << endl;
}