from __future__ import annotations

from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    run_id: str = Field(min_length=1)
    cycle: int = Field(ge=0)
    core_id: int = Field(ge=0)
    metric: str
    value: float
    cache_level: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class MemoryTraceRecord(BaseModel):
    run_id: str = Field(min_length=1)
    cycle: int = Field(ge=0)
    core_id: int = Field(ge=0)
    address: str
    operation: str
    cache_level: str | None = None
    prefetch_outcome: str | None = None
