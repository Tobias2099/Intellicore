# Implementation Summary: gem5 Submodule Workflow

IntelliCore now uses the top-level `gem5/` Git submodule as the single source of truth for gem5 source code. The previous workflow that cloned and built gem5 inside a dedicated prebuilt image has been deprecated.

## Current Design

- `gem5/` is a Git submodule pinned by the parent repository.
- The development Docker image provides the Linux compiler and gem5 build dependencies.
- `gem5-init` builds the submodule with build output stored in the Docker `gem5-build` volume mounted at `/workspace/gem5/build`.
- `gem5-shell`, `gem5-architecture`, synthetic benchmark runs, and PARSEC runs all use `GEM5_ROOT=/workspace/gem5`.
- IntelliCore configs and benchmark assets remain in the parent repository under `configs/gem5/` and `benchmarks/`.

## First-Time Setup

```bash
git submodule update --init --recursive gem5
docker compose --profile dev build dev
docker compose --profile gem5 run --rm gem5-init
```

## Run A Baseline Simulation

```bash
docker compose --profile gem5 run --rm gem5-shell bash -lc \
  'cd "$GEM5_ROOT" && build/${GEM5_ISA:-X86}/${GEM5_BUILD_VARIANT:-gem5.opt} --outdir=/workspace/m5out/intellicore-arch /workspace/configs/gem5/architecture.py'
```

## Run Synthetic Or PARSEC Workloads

Synthetic and PARSEC workloads are still wired through `configs/gem5/multicore_arch.py`. The prepared binaries and inputs stay under:

```text
benchmarks/bin/
benchmarks/parsec/bin/
benchmarks/parsec/inputs/
```

PARSEC source still lives in the `parsec-source` Docker volume managed by `benchmarks/parsec/setup_parsec.py`; that is separate from gem5 source and the `gem5-build` volume.

## Rebuild Rules

You do not need to rebuild gem5 after editing:

- `configs/gem5/*.py`
- benchmark sources or prepared benchmark inputs
- run scripts
- `sim/gem5-intellicore/*`

Rebuild with `gem5-init` when:

- the `gem5/` submodule commit changes
- the `gem5/` source is patched
- `GEM5_ISA` or `GEM5_BUILD_VARIANT` changes
- the `gem5-build` volume or `gem5/build/...` output is missing or stale

## Migration Notes

The old dedicated gem5 image was removed from active workflows. Its important behavior was preserved by moving the needed build dependencies and conservative SCons flags into the dev-image plus `gem5-init` flow.
