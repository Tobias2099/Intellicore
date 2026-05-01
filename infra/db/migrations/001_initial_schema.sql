CREATE TABLE IF NOT EXISTS simulation_runs (
    id TEXT PRIMARY KEY,
    config_name TEXT NOT NULL,
    isa TEXT NOT NULL,
    core_count INTEGER NOT NULL CHECK (core_count > 0),
    deterministic_seed INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS telemetry_events (
    id BIGSERIAL PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES simulation_runs(id) ON DELETE CASCADE,
    cycle BIGINT NOT NULL CHECK (cycle >= 0),
    core_id INTEGER NOT NULL CHECK (core_id >= 0),
    cache_level TEXT,
    metric TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    tags JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS telemetry_events_run_cycle_idx
    ON telemetry_events (run_id, cycle);

CREATE TABLE IF NOT EXISTS memory_trace_records (
    id BIGSERIAL PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES simulation_runs(id) ON DELETE CASCADE,
    cycle BIGINT NOT NULL CHECK (cycle >= 0),
    core_id INTEGER NOT NULL CHECK (core_id >= 0),
    address TEXT NOT NULL,
    operation TEXT NOT NULL,
    cache_level TEXT,
    prefetch_outcome TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS memory_trace_run_core_cycle_idx
    ON memory_trace_records (run_id, core_id, cycle);

CREATE TABLE IF NOT EXISTS area_audit_reports (
    id BIGSERIAL PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES simulation_runs(id) ON DELETE CASCADE,
    agent_area_percent DOUBLE PRECISION NOT NULL CHECK (agent_area_percent >= 0),
    passes_budget BOOLEAN NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
