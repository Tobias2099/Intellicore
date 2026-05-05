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
- `gem5-shell`: Interactive shell using the dev image, with gem5 source/build volumes mounted under `/opt/gem5`.
- `gem5-prebuilt`: Interactive shell using a custom image with gem5 cloned and built under `/opt/gem5`.
- `supabase-check`: One-shot database schema check container that verifies the Supabase telemetry database schema through `DATABASE_URL`.
- `supabase-auto-migrate`: One-shot workflow that upgrades to head, detects SQLAlchemy model changes, generates a migration if needed, applies it, and runs checks.
- `supabase-migrate`: One-shot migration container that runs `alembic upgrade head`, then runs schema and ORM checks.
- `supabase-revision`: One-shot migration generator that runs `alembic revision --autogenerate` and writes a new file under `infra/db/alembic/versions`.
- `supabase-orm-check`: One-shot SQLAlchemy smoke test that inserts, reads, and deletes a temporary simulation run.

### Commands

```bash
# Build the Python/PyTorch/C++/gem5 development image
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
docker compose --profile gem5 run --rm gem5-shell

# Build and run an image that already contains a compiled gem5 checkout
docker compose --profile gem5 build gem5-prebuilt
docker compose --profile gem5 run --rm gem5-prebuilt

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

By default, use the prebuilt gem5 image. It clones gem5 and builds `build/X86/gem5.opt` during the Docker image build. After a successful build, Docker automatically stores the image locally as `intellicore/gem5:local`; no manual `docker save` step is required unless you want to export the image to a tar file for backup or sharing.

Build the image:

```bash
docker compose --profile gem5 build gem5-prebuilt
```

The first build can take a long time because it compiles gem5. A successful build ends with output similar to:

```text
intellicore/gem5:local  Built
```

Check that the image exists locally:

```bash
docker image ls intellicore/gem5:local
```

If the image is present, Docker prints a row for `intellicore/gem5` with the `local` tag. If only the table header appears, the image is not available locally and the build did not finish successfully or was removed.

Run the built image:

```bash
docker compose --profile gem5 run --rm gem5-prebuilt
```

Once the shell prompt changes to something like `root@...:/workspace#`, you are inside the container. Test that gem5 is present and runnable:

```bash
$GEM5_ROOT/build/X86/gem5.opt --help
ls -lh $GEM5_ROOT/build/X86/gem5.opt
```

Leave the container with:

```bash
exit
```

If you want to bypass Compose and run the saved image directly:

```bash
docker run --rm -it \
  -v "$PWD:/workspace" \
  -w /workspace \
  -e GEM5_ROOT=/opt/gem5 \
  -e PYTHONPATH=/workspace/services/control-plane/src:/workspace/services/training/src \
  intellicore/gem5:local bash
```

To export the built image to a portable file:

```bash
docker save -o intellicore-gem5-local.tar intellicore/gem5:local
```

Load that file on another machine with:

```bash
docker load -i intellicore-gem5-local.tar
```

You can pin gem5 to a branch, tag, or commit:

```bash
docker compose --profile gem5 build --build-arg GEM5_REF=stable gem5-prebuilt
```

The prebuilt image defaults to `build/X86/gem5.opt`. Override `GEM5_ISA`, `GEM5_BUILD_VARIANT`, or `GEM5_BUILD_JOBS` to build another target or tune compile parallelism.

### Backup Manual gem5 Build

Use this fallback only if you are working in the lighter `dev` container and want to clone/build gem5 manually instead of using `gem5-prebuilt`.

```bash
docker compose --profile dev up -d dev
docker compose exec dev bash
git clone https://gem5.googlesource.com/public/gem5 "$GEM5_ROOT"
cd "$GEM5_ROOT"
scons build/X86/gem5.opt -j"$(nproc)"
```

## Local Python Commands

If the Python packages are available locally, the starter CLIs can also be run without Docker:

```bash
$env:PYTHONPATH="services/control-plane/src;services/training/src"
python -m intellicore_control.cli runs plan --config configs/gem5/baseline-x86.yaml
python -m intellicore_training.cli train --config configs/agents/baseline-dqn.yaml
```

The generated code is intentionally lightweight boilerplate. It defines stable module boundaries and data contracts so gem5 integration, MARL policies, telemetry ingestion, and dashboard work can evolve independently.
