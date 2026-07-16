# IntelliCore gem5 Extension

This directory contains IntelliCore-owned SimObjects and C++ code that compile
against gem5. It is an out-of-tree gem5 extension, not a gem5 source checkout.

gem5 discovers this directory through its `EXTRAS` SCons option:

```bash
scons build/X86/gem5.opt EXTRAS=/path/to/telemetry/gem5_extension
```

Do not copy these files into `gem5/src`. Keep the upstream gem5 checkout
unmodified.
