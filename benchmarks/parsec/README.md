# PARSEC Benchmarks

IntelliCore keeps PARSEC experiment metadata and orchestration in this
directory, but does not vendor PARSEC source code, generated binaries, disk
images, or large input sets. The full PARSEC source tree should live in the
`parsec-source` Docker volume; only prepared local artifacts are copied into
the ignored `bin/` and `inputs/` folders.

## Layout

```text
benchmarks/parsec/
  README.md
  README-setup.md
  workloads.yaml
  setup_parsec.py
  env.sh
  build.sh
  run-gem5.sh
  bin/           # ignored: copied runnable benchmark binaries
  inputs/        # ignored except inputs/README.md
  source/        # ignored: avoid using this on Windows
  install/       # ignored: local PARSEC build/install output
  disk-image/    # full-system disk-image workflow scaffold
```

## Current Status

Prepared successfully with `simsmall` inputs:

```text
blackscholes
bodytrack
canneal
dedup
facesim
ferret
fluidanimate
freqmine
streamcluster
swaptions
x264
```

Deferred for now:

```text
raytrace
vips
```

`raytrace` and `vips` need extra OS packages in the development image. The
Dockerfile includes the core gem5 build packages; add any missing PARSEC
packages to `infra/docker/dev.Dockerfile` and rebuild `dev` before retrying.

The prepared workloads above are wired into `configs/gem5/multicore_arch.py`
for SE-mode gem5 execution with `simsmall`, `simmedium`, and `simlarge`
argument sets. Prepare the matching input size before running it.

## Setup

Use the setup helper from the IntelliCore repo root:

```bash
py benchmarks/parsec/setup_parsec.py --workload all --input simsmall --keep-going
```

If `py` is not available:

```bash
python benchmarks/parsec/setup_parsec.py --workload all --input simsmall --keep-going
```

Useful variants:

```bash
py benchmarks/parsec/setup_parsec.py --workload blackscholes --input simsmall
py benchmarks/parsec/setup_parsec.py --workload blackscholes,canneal,dedup --input simsmall
py benchmarks/parsec/setup_parsec.py --workload all --input all --keep-going
py benchmarks/parsec/setup_parsec.py --workload dedup --input simsmall --force-build
```

The script creates or reuses the `parsec-source` Docker volume, clones PARSEC
there, downloads the simulator input archive from the mirror, builds workloads,
extracts inputs, and copies prepared artifacts into:

```text
benchmarks/parsec/bin/
benchmarks/parsec/inputs/<input-size>/<workload>/
```

## Run A Workload In gem5

Run a prepared workload with:

```bash
bash benchmarks/parsec/run-gem5.sh blackscholes simsmall
```

From Git Bash, if Docker path conversion interferes, use:

```bash
MSYS_NO_PATHCONV=1 bash benchmarks/parsec/run-gem5.sh blackscholes simsmall
```

Substitute another prepared workload, for example:

```bash
MSYS_NO_PATHCONV=1 bash benchmarks/parsec/run-gem5.sh canneal simsmall
MSYS_NO_PATHCONV=1 bash benchmarks/parsec/run-gem5.sh swaptions simsmall
```

The run writes gem5 output under:

```text
m5out/parsec/<workload>/<input-size>/<policy>/<prefetch>/stats.txt
```

Summarize a completed run:

```bash
py scripts/summarize_stats.py m5out/parsec/blackscholes/simsmall/LRU/delta
```

Normal gem5/PARSEC SE-mode output may include warnings such as ignored
`mprotect`/`rseq` syscalls and:

```text
Can't open /dev/mem: No such file or directory
```

Those messages are expected in syscall-emulation mode. A run is considered
successful when gem5 exits with a message like:

```text
Exiting @ tick ... because exiting with last active thread context
```

## Full-System Path

The upstream gem5 PARSEC tutorial uses gem5art, a Linux kernel, and a PARSEC
disk image. IntelliCore keeps a placeholder for that flow under
`benchmarks/parsec/disk-image/` so full-system assets can be built locally
without becoming repository contents.

Use the full-system path when you need benchmark behavior that depends on a
complete Linux environment, larger input sets, or closer alignment with the
gem5art tutorial.
