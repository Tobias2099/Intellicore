# PARSEC Setup Walkthrough

This guide shows the known-good Git Bash workflow for preparing PARSEC
workload artifacts for IntelliCore.

## What This Creates

The setup helper copies prepared local artifacts into:

```text
benchmarks/parsec/bin/<workload>
benchmarks/parsec/inputs/<input-size>/<workload>/
```

These files are ignored by Git because they are external/generated benchmark
assets.

## Important Notes

Run commands from the IntelliCore repo root.

Do not clone the full PARSEC source tree into `benchmarks/parsec/source/` on
Windows. Use the Docker volume managed by `setup_parsec.py` instead. PARSEC
contains filenames that are awkward on Windows filesystems, while Docker's
Linux volume handles them cleanly.

If you run Docker commands manually from Git Bash, prefix them with
`MSYS_NO_PATHCONV=1` so Git Bash does not rewrite Linux container paths such as
`/workspace`.

## Prepare Workloads

Prepare the currently practical PARSEC set with `simsmall` inputs:

```bash
py benchmarks/parsec/setup_parsec.py --workload all --input simsmall --keep-going
```

If `py` is not available:

```bash
python benchmarks/parsec/setup_parsec.py --workload all --input simsmall --keep-going
```

This command:

- creates or reuses the `parsec-source` Docker volume
- clones `darchr/parsec-benchmark` into that volume
- downloads PARSEC simulator inputs from the working GitHub mirror
- applies the `dedup` GCC compatibility patch
- builds workloads
- extracts selected input archives
- copies binaries and inputs into `benchmarks/parsec/`

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

`raytrace` and `vips` need extra OS packages in the gem5 Docker image. The
Dockerfiles include those packages now, but preparing those workloads requires
rebuilding `gem5-prebuilt`, which may take a long time.

## Useful Setup Variants

Prepare one workload:

```bash
py benchmarks/parsec/setup_parsec.py --workload blackscholes --input simsmall
```

Prepare a subset:

```bash
py benchmarks/parsec/setup_parsec.py --workload blackscholes,canneal,dedup --input simsmall
```

Prepare all simulator input sizes:

```bash
py benchmarks/parsec/setup_parsec.py --workload all --input all --keep-going
```

Force a rebuild:

```bash
py benchmarks/parsec/setup_parsec.py --workload dedup --input simsmall --force-build
```

## Verify Prepared Artifacts

Check binaries:

```bash
ls benchmarks/parsec/bin
```

Check `simsmall` inputs:

```bash
ls benchmarks/parsec/inputs/simsmall
```

You should see the prepared workload names in both locations.

## Run A gem5 Smoke Test

Prepared workloads are wired into `configs/gem5/multicore_arch.py` for
SE-mode gem5 execution. Start with one small smoke test:

```bash
MSYS_NO_PATHCONV=1 bash benchmarks/parsec/run-gem5.sh blackscholes simsmall
```

Other examples:

```bash
MSYS_NO_PATHCONV=1 bash benchmarks/parsec/run-gem5.sh canneal simsmall
MSYS_NO_PATHCONV=1 bash benchmarks/parsec/run-gem5.sh swaptions simsmall
```

This writes gem5 output to:

```text
m5out/parsec/<workload>/<input-size>/LRU/delta/
```

The main result file is:

```text
m5out/parsec/blackscholes/simsmall/LRU/delta/stats.txt
```

Summarize the result:

```bash
py scripts/summarize_stats.py m5out/parsec/blackscholes/simsmall/LRU/delta
```

If `py` is not available:

```bash
python scripts/summarize_stats.py m5out/parsec/blackscholes/simsmall/LRU/delta
```

It is normal to see gem5/PARSEC SE-mode warnings such as ignored `mprotect` or
`rseq` syscalls and:

```text
Can't open /dev/mem: No such file or directory
```

That message comes from PARSEC hook support running without a full Linux guest.
The important success signal is:

```text
Exiting @ tick ... because exiting with last active thread context
```
