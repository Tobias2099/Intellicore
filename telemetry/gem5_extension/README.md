# IntelliCore gem5 Extension

This directory contains IntelliCore-owned SimObjects and C++ code that compile
against gem5. It is an out-of-tree gem5 extension, not a gem5 source checkout.

gem5 discovers this directory through its `EXTRAS` SCons option:

```bash
scons build/X86/gem5.opt EXTRAS=/path/to/telemetry/gem5_extension
```

Do not copy these files into `gem5/src`. Keep the upstream gem5 checkout
unmodified.

`Gem5TelemetryProbe.manager` must contain every cache whose `Hit` and `Miss`
events should update telemetry.

The two-bit per-line saturation counter advances only on cache access probe
callbacks. An accessed line increments up to 3 while other tracked lines in
the same cache decrement toward 0. It does not use a CPU cycle poller.

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
