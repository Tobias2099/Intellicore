# IntelliCore

IntelliCore is a research monorepo for a MARL-driven cache coordination system. The platform is organized around the project requirements: cycle-accurate gem5 simulation, Python-based agent training, PostgreSQL telemetry storage, and a Visual-Stats dashboard for performance analysis.

## Workspace Layout

```text
apps/
  visual-stats/          React dashboard for telemetry and heatmaps
services/
  control-plane/         IntelliCore CLI and simulation orchestration
  training/              MARL training and trace processing
sim/
  gem5-intellicore/      C++ gem5 integration stubs
packages/
  contracts/             Shared JSON schemas and event contracts
infra/
  db/                    PostgreSQL migrations
configs/
  agents/                Agent hyperparameter presets
  gem5/                  Baseline simulator configurations
benchmarks/              Benchmark manifests and workload metadata
docs/
  architecture/          Architecture notes and requirement mapping
scripts/                 Local developer automation
```

## First Milestone

Sprint 1 focuses on a runnable simulation foundation:

- initialize gem5 with standard x86/ARM-style configuration files
- log deterministic baseline telemetry such as IPC, MPKI, AMAL, and EDP
- export traces to a relational store for analysis
- provide early dashboard and CLI surfaces for architecture experiments

## Quick Start

```bash
cp .env.example .env
docker compose up -d postgres
python -m intellicore_control runs plan --config configs/gem5/baseline-x86.yaml
python -m intellicore_training train --config configs/agents/baseline-dqn.yaml
```

The generated code is intentionally lightweight boilerplate. It defines stable module boundaries and data contracts so gem5 integration, MARL policies, telemetry ingestion, and dashboard work can evolve independently.
