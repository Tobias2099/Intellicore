# Data Flow

```mermaid
flowchart LR
    Gem5["gem5 simulation"] --> Adapter["sim/gem5-intellicore"]
    Adapter --> Trace["Memory trace records"]
    Trace --> Control["services/control-plane"]
    Control --> Postgres["Supabase Postgres telemetry store"]
    Postgres --> Dashboard["apps/visual-stats"]
    Postgres --> Training["services/training"]
    Training --> Agent["Agent policy artifacts"]
    Agent --> Adapter
```

The scaffold keeps the cycle-accurate simulation boundary separate from Python training. C++ code should emit normalized trace and telemetry events; Python services validate, persist, and replay them.
