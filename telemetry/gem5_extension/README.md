# IntelliCore gem5 Extension

This directory contains IntelliCore-owned SimObjects and C++ code that compile
against gem5. Most telemetry code is an out-of-tree extension. The exact
replacement event additionally requires the small cache probe-point change in
the repository's pinned `gem5/` submodule.

gem5 discovers this directory through its `EXTRAS` SCons option:

```bash
scons build/X86/gem5.opt EXTRAS=/path/to/telemetry/gem5_extension
```

Do not copy these files into `gem5/src`.

`Gem5TelemetryProbe.manager` contains the owning core's L1 data cache. The
repository configuration creates one probe per core and configures L1D as an
8-way set-associative cache.

The two-bit per-line saturation counter advances only on cache access probe
callbacks. An accessed line increments up to 3 while other tracked lines in
the same cache decrement toward 0. It does not use a CPU cycle poller.

On a demand miss, the probe emits the 16-byte memory trace first and attaches
that trace's `recordCounter` to gem5's `Request`. The request survives MSHR
queuing and reaches allocation on fill. If allocation replaces a valid line,
gem5 emits `Replacement` with the trigger packet and an immutable pre-eviction
snapshot of the set. The 16-byte eviction snapshot reuses the trace's
`recordCounter`; no `parentRecordCounter` or payload growth is required.

Eviction snapshot `fields[0]` through `fields[7]` are physical L1D ways 0
through 7. `lruRank` is the line's true access-recency rank, tracked
independently of the active replacement policy: 0 is the least recently used
valid line and 7 is the most recently used line in a full set. Empty-way fills
do not emit eviction snapshots, and their request linkage is removed at `Fill`.
Each way byte currently stores the two-bit saturation counter, three-bit LRU
rank, dirty bit, and invalid bit. Bit 7 is reserved and emitted as zero until
the separate interval-based access-bit design is implemented; the hardware
prefetch flag is not substituted because it has different semantics.

Each L1D probe currently owns its own per-core `ThreadTelemetryRegistry`.
Sharing one registry across probes, including migration-continuous per-thread
buffers, is a separate integration task. The buffers are intentionally bounded
and expose `tryPopRecord()` for the future Layer 2 consumer. Until that consumer
is wired, long simulations can fill a buffer; `droppedRecords` reports every
record rejected after capacity is reached.

Stock gem5 does not publish per-thread `activate`, `suspend`, or `halt` probe
points. Exact lifecycle-based migration detection therefore requires either
an upstream hook or telemetry-aware CPU subclasses selected by the simulation
configuration. The extension does not silently poll for those transitions.

For the X86 timing CPU used by this repository, instantiate
`X86TelemetryTimingSimpleCPU` instead of `X86TimingSimpleCPU` and assign its
`telemetry_probe` parameter. The subclass forwards lifecycle operations to
gem5's `TimingSimpleCPU` implementation, then compares the context's `cpuId()`
with the registry. Other CPU models require corresponding telemetry-aware
subclasses.
