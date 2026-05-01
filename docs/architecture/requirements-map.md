# Requirements Map

This scaffold maps the requirements document to concrete repository areas.

| Requirement Area | Repository Area | Initial Responsibility |
| --- | --- | --- |
| Architectural configuration management | `configs/gem5`, `services/control-plane` | Validate simulator inputs and produce deterministic run plans. |
| Machine learning control logic | `services/training`, `configs/agents` | Train and package lightweight MARL/prefetch policies. |
| Simulation-to-ML interface | `packages/contracts`, `infra/db`, `services/control-plane` | Normalize traces and telemetry events. |
| Workload characterization logging | `infra/db`, `packages/contracts/schemas` | Store IPC, MPKI, AMAL, EDP, prefetch, and audit data. |
| Performance analysis dashboard | `apps/visual-stats` | Render baseline comparisons and cache locality views. |
| gem5 integration | `sim/gem5-intellicore` | Provide C++ hooks for cache events, hints, and policy decisions. |

## Sprint 1 Scope

The first milestone should prove that a baseline simulation can be configured, run, logged, and inspected. MARL behavior is represented by simple extension points until Sprint 2.
