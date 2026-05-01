from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .config_loader import load_config


class CacheConfig(BaseModel):
    size: str
    associativity: int = Field(gt=0)
    policy: str | None = None


class MemoryConfig(BaseModel):
    type: str
    size: str


class TelemetryConfig(BaseModel):
    metrics: list[str]
    deterministic_seed: int


class Gem5RunConfig(BaseModel):
    name: str
    isa: Literal["x86", "arm", "riscv"]
    cores: int = Field(gt=0)
    clock: str
    memory: MemoryConfig
    caches: dict[str, CacheConfig]
    telemetry: TelemetryConfig

    @classmethod
    def from_yaml(cls, path: Path) -> "Gem5RunConfig":
        return cls.model_validate(load_config(path))


class RunPlan(BaseModel):
    run_id: str
    config_name: str
    isa: str
    cores: int
    metrics: list[str]
    deterministic_seed: int
