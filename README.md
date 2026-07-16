# IntelliCore

IntelliCore is a research monorepo for a MARL-driven cache coordination system. The platform is organized around the project requirements: cycle-accurate gem5 simulation, Python-based agent training, Supabase cloud Postgres telemetry storage, and a Visual-Stats dashboard for performance analysis.

## Repository Structure

```text
.
|-- apps/
|   `-- visual-stats/
|       `-- src/
|-- benchmarks/
|-- configs/
|   |-- agents/
|   `-- gem5/
|-- gem5/                 # Git submodule: upstream gem5 source
|-- docs/
|   `-- architecture/
|-- infra/
|   |-- db/
|   |   |-- alembic/
|   |   `-- migrations/
|   `-- docker/
|-- packages/
|   `-- contracts/
|       `-- schemas/
|-- scripts/
|-- services/
|   |-- control-plane/
|   |   |-- src/intellicore_control/
|   |   `-- tests/
|   `-- training/
|       |-- src/intellicore_training/
|       `-- tests/
`-- sim/
    `-- gem5-intellicore/
        |-- include/intellicore/
        |-- src/
        `-- tests/
```

## Folder Guide

| Path                                              | Purpose                                                                                                                                |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/`                                           | User-facing applications that consume IntelliCore telemetry and research outputs.                                                      |
| `apps/visual-stats/`                              | React/Vite dashboard for performance analysis, metric summaries, and future cache residency heatmaps.                                  |
| `apps/visual-stats/src/`                          | Dashboard source code, styling, and UI components.                                                                                     |
| `benchmarks/`                                     | Benchmark manifests and workload metadata. This is where SPEC, STREAM, synthetic stride, and future workload definitions are tracked.  |
| `configs/`                                        | Versioned configuration files used by services, simulation runs, and agents.                                                           |
| `configs/agents/`                                 | MARL agent and baseline policy presets, including reward weights and inference limits.                                                 |
| `configs/gem5/`                                   | Baseline simulator configurations for ISA, core count, memory, cache hierarchy, and deterministic telemetry settings.                  |
| `gem5/`                                           | Git submodule for the pinned upstream gem5 source used by Docker and local simulation workflows.                                      |
| `docs/`                                           | Project documentation that is not tied to one package.                                                                                 |
| `docs/architecture/`                              | Architecture notes, data-flow diagrams, Docker usage, and requirement-to-module mapping.                                               |
| `infra/`                                          | Infrastructure needed to run or support the project locally and in containers.                                                         |
| `infra/db/`                                       | Database assets for the Supabase telemetry store.                                                                                      |
| `infra/db/migrations/`                            | Legacy SQL schema reference from the first scaffold. New schema changes should use Alembic migrations.                                 |
| `infra/db/alembic/`                               | Alembic migration environment for Supabase automigration.                                                                              |
| `infra/docker/`                                   | Docker image definitions for the research development environment.                                                                     |
| `packages/`                                       | Shared packages used by more than one app or service.                                                                                  |
| `packages/contracts/`                             | Shared event contracts and schema package for simulation, telemetry, and service boundaries.                                           |
| `packages/contracts/schemas/`                     | JSON Schema files for telemetry events and memory trace records.                                                                       |
| `scripts/`                                        | Developer automation and smoke checks. These scripts should be safe to run locally or inside Docker.                                   |
| `services/`                                       | Backend and research services.                                                                                                         |
| `services/control-plane/`                         | Python CLI and orchestration layer for validating gem5 configs, planning deterministic simulation runs, and modeling telemetry events. |
| `services/control-plane/src/intellicore_control/` | Control-plane package source code.                                                                                                     |
| `services/control-plane/tests/`                   | Unit tests for run planning and telemetry models.                                                                                      |
| `services/training/`                              | Python package for MARL training, reward scoring, trace replay, and baseline prefetch policies.                                        |
| `services/training/src/intellicore_training/`     | Training package source code.                                                                                                          |
| `services/training/tests/`                        | Unit tests for reward and policy behavior.                                                                                             |
| `sim/`                                            | Simulator-facing code and C++ integration modules.                                                                                     |
| `sim/gem5-intellicore/`                           | C++ scaffold for gem5 cache-agent integration and smoke tests.                                                                         |
| `sim/gem5-intellicore/include/intellicore/`       | Public C++ headers for cache-agent types and decisions.                                                                                |
| `sim/gem5-intellicore/src/`                       | C++ implementation files.                                                                                                              |
| `sim/gem5-intellicore/tests/`                     | C++ smoke tests for the simulator adapter layer.                                                                                       |

## Root Files

| File                   | Purpose                                                                                                           |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `.dockerignore`        | Keeps local build artifacts, virtualenvs, caches, and Git metadata out of Docker build contexts.                  |
| `.editorconfig`        | Normalizes line endings and indentation across editors.                                                           |
| `.env.example`         | Template for local environment variables, including the Supabase `DATABASE_URL`, `GEM5_ROOT`, and artifact paths. |
| `.gitignore`           | Excludes generated files, build outputs, dependency folders, caches, and local secrets.                           |
| `alembic.ini`          | Alembic configuration for Supabase automigration.                                                                 |
| `docker-compose.yml`   | Docker stack for the Python/PyTorch/C++ dev container, gem5 shell, and Supabase schema checks.                    |
| `package.json`         | Node workspace metadata for frontend apps and shared JavaScript/JSON packages.                                    |
| `pyproject.toml`       | Root Python workspace metadata, test path configuration, and lint settings.                                       |
| `requirements-dev.txt` | Python dependencies installed into the Docker development image.                                                  |

## First Milestone

Sprint 1 focuses on a runnable simulation foundation:

- initialize gem5 with standard x86/ARM-style configuration files
- log deterministic baseline telemetry such as IPC, MPKI, AMAL, and EDP
- export traces to a relational store for analysis
- provide early dashboard and CLI surfaces for architecture experiments

## Quick Start

```bash
cp .env.example .env
docker compose --profile dev build dev
docker compose --profile dev run --rm dev bash scripts/docker-smoke.sh
docker compose --profile tools run --rm supabase-check
```

All `docker compose ...` commands in this README assume your working directory is the IntelliCore repo root (the folder containing `docker-compose.yml`).

If your local workspace has an extra sibling folder (for example a separate `gem5/` checkout) and you are running from the parent directory, pass `-f` explicitly:

```bash
# From /home/zuhairq/Projects/Intellicore (parent folder)
docker compose -f Intellicore/docker-compose.yml --profile gem5 run --rm gem5-architecture
```

Before running commands that touch telemetry, set `DATABASE_URL` in `.env` to the Supabase cloud Postgres connection string.

## Supabase Setup

IntelliCore uses Supabase cloud Postgres as the telemetry store. Tables are modeled with SQLAlchemy in `services/control-plane/src/intellicore_control/db/models.py`, and migrations are managed with Alembic in `infra/db/alembic`.

Fast path after the dev container is running:

```bash
docker compose --profile dev up --build -d dev
docker compose exec -e MIGRATION_MESSAGE="describe schema change" dev python scripts/auto_migrate.py
```

The `exec dev` command reuses the already-built container dependencies. This avoids reinstalling Python packages on every migration run.

By default, auto-migrate refuses to apply destructive or risky autogenerated operations such as `drop_column`, `drop_table`, `drop_index`, `drop_constraint`, raw `op.execute`, type changes, and `nullable=False` changes. Review the generated migration first. If the destructive change is intentional, rerun with:

```bash
docker compose exec -e MIGRATION_MESSAGE="describe schema change" -e ALLOW_DESTRUCTIVE_MIGRATIONS=true dev python scripts/auto_migrate.py
```

One-shot path:

```bash
# Generate/apply migrations from SQLAlchemy model changes, then verify Supabase
docker compose --profile tools run --rm -e MIGRATION_MESSAGE="describe schema change" supabase-auto-migrate

# Allow intentional destructive migrations after reviewing the generated revision
docker compose --profile tools run --rm -e MIGRATION_MESSAGE="describe schema change" -e ALLOW_DESTRUCTIVE_MIGRATIONS=true supabase-auto-migrate

# Apply existing Alembic migrations only
docker compose --profile tools run --rm supabase-migrate

# Verify the required tables without applying migrations
docker compose --profile tools run --rm supabase-check

# Verify the SQLAlchemy ORM can write/read/delete through Supabase
docker compose --profile tools run --rm supabase-orm-check
```

The active Alembic schema creates:

- `projects`
- `hardware_configurations`
- `agent_configurations`
- `simulation_runs`
- `performance_reports`
- `memory_traces`
- `reward_signals`
- `coordination_events`
- `silicon_area_audits`
- `determinism_checks`
- `sprints`
- `user_stories`
- `requirements`
- `test_cases`
- `test_requirement_links`

## Docker Usage

### Services

- `dev`: Long-running development container with Python 3.11, CPU PyTorch, C++ build tools, and gem5 dependencies.
- `gem5-shell`: Interactive shell using the dev image and the `gem5/` submodule at `/workspace/gem5`.
- `gem5-init`: One-shot helper that builds `build/X86/gem5.opt` from the `gem5/` submodule into the Docker `gem5-build` volume.
- `supabase-check`: One-shot database schema check container that verifies the Supabase telemetry database schema through `DATABASE_URL`.
- `supabase-auto-migrate`: One-shot workflow that upgrades to head, detects SQLAlchemy model changes, generates a migration if needed, applies it, and runs checks.
- `supabase-migrate`: One-shot migration container that runs `alembic upgrade head`, then runs schema and ORM checks.
- `supabase-revision`: One-shot migration generator that runs `alembic revision --autogenerate` and writes a new file under `infra/db/alembic/versions`.
- `supabase-orm-check`: One-shot SQLAlchemy smoke test that inserts, reads, and deletes a temporary simulation run.

### Commands

```bash
# Build the Python/PyTorch/C++/gem5 development image
git submodule update --init --recursive gem5
docker compose --profile dev build dev

# Run the full Docker toolchain smoke test
docker compose --profile dev run --rm dev bash scripts/docker-smoke.sh

# Start a persistent development shell
docker compose --profile dev up -d dev
docker compose exec dev bash

# Verify the Supabase telemetry database schema
docker compose --profile tools run --rm supabase-check

# Generate/apply migrations from model changes and verify the schema plus ORM path
docker compose --profile tools run --rm -e MIGRATION_MESSAGE="describe schema change" supabase-auto-migrate

# Intentionally allow destructive operations after migration review
docker compose --profile tools run --rm -e MIGRATION_MESSAGE="describe schema change" -e ALLOW_DESTRUCTIVE_MIGRATIONS=true supabase-auto-migrate

# Apply existing Supabase migrations and verify the schema plus ORM path
docker compose --profile tools run --rm supabase-migrate

# Verify SQLAlchemy ORM access only
docker compose --profile tools run --rm supabase-orm-check

# Open an interactive gem5-oriented shell
docker compose --profile gem5 run --rm gem5-init
docker compose --profile gem5 run --rm gem5-shell

# If the gem5 build fails at the final link step, lower GEM5_BUILD_JOBS in
# docker-compose.yml and rerun gem5-init.

# Stop and remove containers
docker compose down
```

### Faster Dev-Container Commands

The one-shot `supabase-*` services are convenient, but they install Python dependencies each time because they run temporary containers. For repeated work, start the long-running dev container once and use `docker compose exec`.

```bash
# Build and start once
docker compose --profile dev up --build -d dev

# Run automigration without reinstalling dependencies
docker compose exec -e MIGRATION_MESSAGE="describe schema change" dev python scripts/auto_migrate.py

# Run destructive automigrations without reinstalling dependencies
docker compose exec -e MIGRATION_MESSAGE="describe schema change" -e ALLOW_DESTRUCTIVE_MIGRATIONS=true dev python scripts/auto_migrate.py

# Run checks without reinstalling dependencies
docker compose exec dev python scripts/check_db.py
docker compose exec dev python scripts/check_orm.py

# Open a shell in the reusable dev container
docker compose exec dev bash

# Stop when finished
docker compose stop dev
```

On Windows, Docker Desktop is the usual way to provide the Docker engine, but the commands work with any Docker engine that supports Compose.

## gem5 Workflow

### Probe smoke test

The minimal probe test attaches IntelliCore's `IntellicoreProbeSmoke` to a
`CommMonitor`. The probe is compiled from `telemetry/gem5_extension` using
gem5's out-of-tree `EXTRAS` mechanism; the upstream gem5 source tree remains
unmodified.

After running `gem5-init`, run the smoke test with the submodule build:

```bash
docker compose --profile gem5 run --rm gem5-shell bash -lc \
  'cd "$GEM5_ROOT" && build/${GEM5_ISA:-X86}/${GEM5_BUILD_VARIANT:-gem5.opt} \
    --outdir=/workspace/m5out/probe-smoke \
    /workspace/configs/gem5/probe_smoke.py'
```

The smoke test passes when it prints `Intellicore probe smoke test completed:
simulate() limit reached` and `m5out/probe-smoke/stats.txt` contains a nonzero
`system.monitor.intellicore_probe_smoke.events` value. This confirms that
packet events reached IntelliCore's C++ probe callback.

gem5 source lives in the top-level `gem5/` submodule. The Docker image only
provides the Linux build tools; it does not clone or vendor a second gem5
checkout.

Initialize the submodule and build gem5 from it:

```bash
git submodule update --init --recursive gem5
docker compose --profile dev build dev
docker compose --profile gem5 run --rm gem5-init
```

The first `gem5-init` run can take a while because it compiles gem5. The build output is stored in Docker's `gem5-build` volume mounted at:

```text
/workspace/gem5/build/X86/gem5.opt
```

Open an interactive shell with the submodule mounted at `$GEM5_ROOT`:

```bash
docker compose --profile gem5 run --rm gem5-shell
```

Inside the container, test that gem5 is present and runnable:

```bash
$GEM5_ROOT/build/$GEM5_ISA/$GEM5_BUILD_VARIANT --help
ls -lh $GEM5_ROOT/build/$GEM5_ISA/$GEM5_BUILD_VARIANT
```

Run IntelliCore's baseline architecture config using the submodule build (writes outputs under `m5out/intellicore-arch` on the host):

```bash
docker compose --profile gem5 run --rm gem5-shell bash -lc \
  'cd "$GEM5_ROOT" && build/${GEM5_ISA:-X86}/${GEM5_BUILD_VARIANT:-gem5.opt} --outdir=/workspace/m5out/intellicore-arch /workspace/configs/gem5/architecture.py'
```

To update gem5, update the submodule and commit the new parent-repo pointer:

```bash
cd gem5
git fetch --tags
git checkout <tag-or-commit>
cd ..
git add gem5
```

Editing files under `configs/gem5/`, `benchmarks/`, or `sim/` does not require rebuilding gem5. Rerun `gem5-init` only when the gem5 submodule source changes, the selected ISA or binary variant changes, or the `gem5-build` volume/build output is missing.

### Multicore LRU Config

`configs/gem5/multicore_LRU.py` defines a classic-cache multicore simulation with four X86 timing CPUs, private L1 instruction/data caches, a shared L2 cache, DDR3 memory, and LRU replacement policies.

The config runs the synthetic C++ benchmark at `benchmarks/src/memory_patterns.cpp`. The benchmark allocates a large integer array and then reads it with one of four access patterns:

- `sequential`: reads `arr[0]`, `arr[1]`, `arr[2]`, and so on. This has good spatial locality.
- `stride`: reads every 16th integer, which is about one 64-byte cache line on common systems. This uses less of each fetched cache line.
- `random`: shuffles an index array once, then reads `arr[idx[i]]`. This creates poor locality and should usually cause more cache misses.
- `hotcold`: repeatedly reuses a small hot region, streams through a larger cold region, then reuses the hot region again. This creates eviction pressure and is intended to make replacement-policy differences easier to observe.

The benchmark accumulates each loaded value into `sum` and prints the result. The value of `sum` is not the performance metric; it prevents the compiler from optimizing away the memory reads.

The benchmark accepts an optional second argument for the number of array elements and an optional third argument for worker threads. For gem5 smoke runs, the multicore config defaults to one worker thread because pthread-heavy syscall-emulation runs can fail before the simulation data is useful. It uses `1048576` elements by default, which is about 4 MiB of integer array data before random-mode index storage.

Compile the benchmark inside the gem5 shell so gem5 receives a Linux executable:

```bash
docker compose --profile gem5 run --rm gem5-shell \
  bash -lc 'mkdir -p /workspace/benchmarks/bin && g++ -O2 -std=c++17 -static /workspace/benchmarks/src/memory_patterns.cpp -o /workspace/benchmarks/bin/memory_patterns'
```

Windows Git Bash or VS Code Bash variant:

```bash
MSYS_NO_PATHCONV=1 docker compose --profile gem5 run --rm gem5-shell \
  bash -lc 'mkdir -p /workspace/benchmarks/bin && g++ -O2 -std=c++17 -static /workspace/benchmarks/src/memory_patterns.cpp -o /workspace/benchmarks/bin/memory_patterns'
```

`configs/gem5/multicore_LRU.py` points gem5 at that executable:

```python
binary = "/workspace/benchmarks/bin/memory_patterns"
```

The selected benchmark mode is passed through `process.cmd`:

```python
modes = ["sequential", "stride", "random", "hotcold"]
selected_mode = modes[0]
benchmark_size = "1048576"
process.cmd = [binary, selected_mode, benchmark_size]
```

Change `selected_mode` to `modes[1]` for `stride`, `modes[2]` for `random`, or `modes[3]` for `hotcold`. With the current multicore config, every CPU runs the same benchmark mode.


Run it with the submodule gem5 build, selecting eviction policy and access pattern.

Example (LRU policy, stride pattern, delta prefetcher) — this writes outputs to `/workspace/m5out/LRU/stride` on the host:

```bash
docker compose --profile gem5 run --rm -e POLICY=LRU -e MODE=stride -e PREFETCH=delta gem5-shell \
  bash -lc 'cd "$GEM5_ROOT" && \
    build/${GEM5_ISA:-X86}/${GEM5_BUILD_VARIANT:-gem5.opt} --outdir=/workspace/m5out/$POLICY/$MODE \
    /workspace/configs/gem5/multicore_LRU.py --repl $POLICY --mode $MODE --prefetch $PREFETCH'
```

Template (substitute values; default prefetcher is `delta` — choose `none`, `stride`, `tagged`, or `delta`):

```bash
docker compose --profile gem5 run --rm -e POLICY=<LRU|LFU|MRU> -e MODE=<sequential|stride|random|hotcold> -e PREFETCH=<none|stride|tagged|delta> \
  gem5-shell bash -lc 'cd "$GEM5_ROOT" && \
    build/${GEM5_ISA:-X86}/${GEM5_BUILD_VARIANT:-gem5.opt} --outdir=/workspace/m5out/$POLICY/$MODE \
    /workspace/configs/gem5/multicore_LRU.py --repl $POLICY --mode $MODE --prefetch $PREFETCH'
```

Windows Git Bash or VS Code Bash variant (MSYS path conversion disabled):

```bash
MSYS_NO_PATHCONV=1 docker compose --profile gem5 run --rm -e POLICY=LRU -e MODE=stride gem5-shell \
  bash -lc 'cd "$GEM5_ROOT" && \
    build/${GEM5_ISA:-X86}/${GEM5_BUILD_VARIANT:-gem5.opt} --outdir=/workspace/m5out/$POLICY/$MODE \
    /workspace/configs/gem5/multicore_LRU.py --repl $POLICY --mode $MODE'
```

Editing files under `configs/gem5/` does not require rebuilding gem5 because the repository is mounted into the container at `/workspace`.

gem5 writes simulation output under the directory passed to `--outdir`. The example above writes `m5out/sequential/stats.txt` on the host. If `--outdir` is omitted, gem5 uses the default `m5out/stats.txt`, which is fine for a smoke test but will be overwritten by the next run.

Use separate output folders when comparing modes:

```bash
docker compose --profile gem5 run --rm gem5-shell \
  bash -lc '$GEM5_ROOT/build/${GEM5_ISA:-X86}/${GEM5_BUILD_VARIANT:-gem5.opt} --outdir=/workspace/m5out/stride /workspace/configs/gem5/multicore_LRU.py'

docker compose --profile gem5 run --rm gem5-shell \
  bash -lc '$GEM5_ROOT/build/${GEM5_ISA:-X86}/${GEM5_BUILD_VARIANT:-gem5.opt} --outdir=/workspace/m5out/random /workspace/configs/gem5/multicore_LRU.py'
```

Windows Git Bash or VS Code Bash variants:

```bash
MSYS_NO_PATHCONV=1 docker compose --profile gem5 run --rm gem5-shell \
  bash -lc '$GEM5_ROOT/build/${GEM5_ISA:-X86}/${GEM5_BUILD_VARIANT:-gem5.opt} --outdir=/workspace/m5out/stride /workspace/configs/gem5/multicore_LRU.py'

MSYS_NO_PATHCONV=1 docker compose --profile gem5 run --rm gem5-shell \
  bash -lc '$GEM5_ROOT/build/${GEM5_ISA:-X86}/${GEM5_BUILD_VARIANT:-gem5.opt} --outdir=/workspace/m5out/random /workspace/configs/gem5/multicore_LRU.py'
```

The benchmark's own `cout` output appears in the gem5 run log. Cache and timing counters appear in `stats.txt`.

Use `scripts/summarize_stats.py` to print the important fields in a compact, readable form. By default it scans every `m5out/**/stats.txt` file and reports the benchmark name, L1D miss rate, L1D misses per CPU core, L2 miss rate, IPC, and simulated seconds:

```bash
docker compose --profile dev run --rm dev python scripts/summarize_stats.py
```

To summarize one run, pass either the run directory or the `stats.txt` file:

```bash
docker compose --profile dev run --rm dev python scripts/summarize_stats.py m5out/stride
docker compose --profile dev run --rm dev python scripts/summarize_stats.py m5out/stride/stats.txt
```

### PARSEC Benchmarks

PARSEC integration lives under `benchmarks/parsec/`. IntelliCore tracks the
metadata, scripts, and documentation there, but does not commit PARSEC source,
compiled binaries, disk images, or large input sets.

For the first SE-mode smoke test, place or build these local files:

```text
benchmarks/parsec/bin/blackscholes
benchmarks/parsec/inputs/simsmall/blackscholes/in_4K.txt
```

If you have a PARSEC source tree available, place it at
`benchmarks/parsec/source/` or set `PARSEC_ROOT`, then build inside the gem5
shell:

```bash
docker compose --profile gem5 run --rm gem5-shell \
  bash /workspace/benchmarks/parsec/build.sh blackscholes
```

Run the PARSEC `blackscholes` smoke test:

```bash
bash benchmarks/parsec/run-gem5.sh blackscholes simsmall
```

This invokes `configs/gem5/multicore_arch.py` with `--benchmark parsec` and
writes results under:

```text
m5out/parsec/blackscholes/simsmall/<policy>/<prefetch>/stats.txt
```

The upstream gem5 tutorial's full-system path is scaffolded under
`benchmarks/parsec/disk-image/`. Use that path when you want a PARSEC disk image,
Linux guest execution, and closer alignment with gem5art-style experiments.

For deeper manual inspection, grep the raw gem5 stats:

```bash
grep -i "miss" m5out/sequential/stats.txt
grep -i "miss" m5out/stride/stats.txt
grep -i "miss" m5out/random/stats.txt
grep -i "miss" m5out/hotcold/stats.txt
```

### Manual gem5 Build

```bash
git submodule update --init --recursive gem5
docker compose --profile dev up -d dev
docker compose exec dev bash
cd "$GEM5_ROOT"
scons "build/${GEM5_ISA:-X86}/${GEM5_BUILD_VARIANT:-gem5.opt}" -j"$(nproc)"
```

## Local Python Commands

If the Python packages are available locally, the starter CLIs can also be run without Docker:

```bash
$env:PYTHONPATH="services/control-plane/src;services/training/src"
python -m intellicore_control.cli runs plan --config configs/gem5/baseline-x86.yaml
python -m intellicore_training.cli train --config configs/agents/baseline-dqn.yaml
```

The generated code is intentionally lightweight boilerplate. It defines stable module boundaries and data contracts so gem5 integration, MARL policies, telemetry ingestion, and dashboard work can evolve independently.
