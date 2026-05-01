from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as SQLEnum


class Base(DeclarativeBase):
    pass


class CpuIsa(enum.StrEnum):
    X86 = "x86"
    ARM = "ARM"


class CpuMode(enum.StrEnum):
    ATOMIC = "atomic"
    TIMING_SIMPLE = "timing_simple"
    O3 = "o3"


class CacheLevel(enum.StrEnum):
    L1 = "L1"
    L2 = "L2"
    LLC = "LLC"


class CacheEventType(enum.StrEnum):
    HIT = "HIT"
    MISS = "MISS"
    EVICTION = "EVICTION"
    PREFETCH_FILL = "PREFETCH_FILL"


class StrideType(enum.StrEnum):
    CONSTANT = "CONSTANT"
    IRREGULAR = "IRREGULAR"
    STREAMING = "STREAMING"


class PrefetchOutcome(enum.StrEnum):
    USEFUL = "useful"
    LATE = "late"
    WASTED = "wasted"


class PriorityLevel(enum.StrEnum):
    MUST_HAVE = "must_have"
    SHOULD_HAVE = "should_have"
    COULD_HAVE = "could_have"
    WONT_HAVE = "wont_have"


class SprintStatus(enum.StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class StoryStatus(enum.StrEnum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class AuditDecision(enum.StrEnum):
    APPROVED = "approved"
    FLAGGED = "flagged"


cpu_isa_enum = SQLEnum(CpuIsa, name="cpu_isa", values_callable=lambda values: [item.value for item in values])
cpu_mode_enum = SQLEnum(CpuMode, name="cpu_mode", values_callable=lambda values: [item.value for item in values])
cache_level_enum = SQLEnum(
    CacheLevel,
    name="cache_level",
    values_callable=lambda values: [item.value for item in values],
)
cache_event_type_enum = SQLEnum(
    CacheEventType,
    name="cache_event_type",
    values_callable=lambda values: [item.value for item in values],
)
stride_type_enum = SQLEnum(
    StrideType,
    name="stride_type",
    values_callable=lambda values: [item.value for item in values],
)
prefetch_outcome_enum = SQLEnum(
    PrefetchOutcome,
    name="prefetch_outcome",
    values_callable=lambda values: [item.value for item in values],
)
priority_level_enum = SQLEnum(
    PriorityLevel,
    name="priority_level",
    values_callable=lambda values: [item.value for item in values],
)
sprint_status_enum = SQLEnum(
    SprintStatus,
    name="sprint_status",
    values_callable=lambda values: [item.value for item in values],
)
story_status_enum = SQLEnum(
    StoryStatus,
    name="story_status",
    values_callable=lambda values: [item.value for item in values],
)
audit_decision_enum = SQLEnum(
    AuditDecision,
    name="audit_decision",
    values_callable=lambda values: [item.value for item in values],
)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    hardware_configurations: Mapped[list[HardwareConfiguration]] = relationship(back_populates="project")
    agent_configurations: Mapped[list[AgentConfiguration]] = relationship(back_populates="project")
    simulation_runs: Mapped[list[SimulationRun]] = relationship(back_populates="project")
    sprints: Mapped[list[Sprint]] = relationship(back_populates="project")
    requirements: Mapped[list[Requirement]] = relationship(back_populates="project")
    test_cases: Mapped[list[TestCase]] = relationship(back_populates="project")


class HardwareConfiguration(Base):
    __tablename__ = "hardware_configurations"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    isa: Mapped[CpuIsa] = mapped_column(cpu_isa_enum, nullable=False)
    core_count: Mapped[int] = mapped_column(Integer, nullable=False)
    l1_size_kb: Mapped[int] = mapped_column(Integer, nullable=False)
    l2_size_kb: Mapped[int] = mapped_column(Integer, nullable=False)
    llc_size_kb: Mapped[int] = mapped_column(Integer, nullable=False)
    l1_associativity: Mapped[int] = mapped_column(Integer, nullable=False)
    l2_associativity: Mapped[int] = mapped_column(Integer, nullable=False)
    llc_associativity: Mapped[int] = mapped_column(Integer, nullable=False)
    llc_inclusive: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    config_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    project: Mapped[Project | None] = relationship(back_populates="hardware_configurations")
    simulation_runs: Mapped[list[SimulationRun]] = relationship(back_populates="hardware_configuration")

    __table_args__ = (
        CheckConstraint("core_count BETWEEN 1 AND 16", name="hardware_configurations_core_count_range"),
    )


class AgentConfiguration(Base):
    __tablename__ = "agent_configurations"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    learning_rate: Mapped[float] = mapped_column(Float, nullable=False)
    reward_hit: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("1.0"))
    reward_miss: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("-1.0"))
    reward_wasted_prefetch: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("-0.5"))
    reward_late_prefetch: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("-0.2"))
    weight_matrix_kb: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Must stay under 64KB per core per NF122",
    )
    inference_cycles: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Must stay under 3 cycles per NF121",
    )
    model_file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    project: Mapped[Project | None] = relationship(back_populates="agent_configurations")
    simulation_runs: Mapped[list[SimulationRun]] = relationship(back_populates="agent_configuration")
    silicon_area_audits: Mapped[list[SiliconAreaAudit]] = relationship(back_populates="agent_configuration")


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    project_id: Mapped[UUID | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    hardware_config_id: Mapped[UUID | None] = mapped_column(ForeignKey("hardware_configurations.id"), nullable=True)
    agent_config_id: Mapped[UUID | None] = mapped_column(ForeignKey("agent_configurations.id"), nullable=True)
    is_baseline: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    cpu_mode: Mapped[CpuMode] = mapped_column(cpu_mode_enum, nullable=False)
    benchmark_name: Mapped[str] = mapped_column(Text, nullable=False)
    simpoint_used: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    random_seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    instruction_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    wall_clock_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'"))
    output_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    project: Mapped[Project | None] = relationship(back_populates="simulation_runs")
    hardware_configuration: Mapped[HardwareConfiguration | None] = relationship(back_populates="simulation_runs")
    agent_configuration: Mapped[AgentConfiguration | None] = relationship(back_populates="simulation_runs")
    performance_reports: Mapped[list[PerformanceReport]] = relationship(back_populates="simulation_run")
    memory_traces: Mapped[list[MemoryTrace]] = relationship(back_populates="simulation_run")
    reward_signals: Mapped[list[RewardSignal]] = relationship(back_populates="simulation_run")
    coordination_events: Mapped[list[CoordinationEvent]] = relationship(back_populates="simulation_run")
    silicon_area_audits: Mapped[list[SiliconAreaAudit]] = relationship(back_populates="simulation_run")


class PerformanceReport(Base):
    __tablename__ = "performance_reports"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    simulation_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("simulation_runs.id", ondelete="CASCADE"),
        nullable=True,
    )
    final_ipc: Mapped[float] = mapped_column(Float, nullable=False)
    final_mpki: Mapped[float] = mapped_column(Float, nullable=False)
    amal_cycles: Mapped[float] = mapped_column(Float, nullable=False)
    edp: Mapped[float | None] = mapped_column(Float, nullable=True)
    prefetcher_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    inference_overhead: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_instructions: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    total_cycles: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    l1_hit_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    l1_miss_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    l2_hit_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    l2_miss_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    llc_hit_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    llc_miss_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    dram_accesses: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    simulation_run: Mapped[SimulationRun | None] = relationship(back_populates="performance_reports")


class MemoryTrace(Base):
    __tablename__ = "memory_traces"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    simulation_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("simulation_runs.id", ondelete="CASCADE"),
        nullable=True,
    )
    cycle_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    core_id: Mapped[int] = mapped_column(Integer, nullable=False)
    cache_level: Mapped[CacheLevel] = mapped_column(cache_level_enum, nullable=False)
    memory_address: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[CacheEventType] = mapped_column(cache_event_type_enum, nullable=False)
    stride_type: Mapped[StrideType | None] = mapped_column(stride_type_enum, nullable=True)
    prefetch_outcome: Mapped[PrefetchOutcome | None] = mapped_column(prefetch_outcome_enum, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    simulation_run: Mapped[SimulationRun | None] = relationship(back_populates="memory_traces")

    __table_args__ = (
        Index("idx_memory_traces_run", "simulation_run_id"),
        Index("idx_memory_traces_cycle", "simulation_run_id", "cycle_timestamp"),
        Index("idx_memory_traces_address", "memory_address"),
    )


class RewardSignal(Base):
    __tablename__ = "reward_signals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    simulation_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("simulation_runs.id", ondelete="CASCADE"),
        nullable=True,
    )
    agent_id: Mapped[int] = mapped_column(Integer, nullable=False)
    cycle_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reward_value: Mapped[float] = mapped_column(Float, nullable=False)
    delta_hit_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    delta_amal: Mapped[float | None] = mapped_column(Float, nullable=True)
    action_taken: Mapped[str] = mapped_column(Text, nullable=False)
    target_address: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    simulation_run: Mapped[SimulationRun | None] = relationship(back_populates="reward_signals")

    __table_args__ = (
        Index("idx_reward_signals_run", "simulation_run_id"),
        Index("idx_reward_signals_agent", "simulation_run_id", "agent_id"),
    )


class CoordinationEvent(Base):
    __tablename__ = "coordination_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    simulation_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("simulation_runs.id", ondelete="CASCADE"),
        nullable=True,
    )
    cycle_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_core_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_core_id: Mapped[int] = mapped_column(Integer, nullable=False)
    memory_address: Mapped[int] = mapped_column(BigInteger, nullable=False)
    was_beneficial: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    simulation_run: Mapped[SimulationRun | None] = relationship(back_populates="coordination_events")

    __table_args__ = (Index("idx_coordination_run", "simulation_run_id"),)


class SiliconAreaAudit(Base):
    __tablename__ = "silicon_area_audits"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    agent_config_id: Mapped[UUID | None] = mapped_column(ForeignKey("agent_configurations.id"), nullable=True)
    simulation_run_id: Mapped[UUID | None] = mapped_column(ForeignKey("simulation_runs.id"), nullable=True)
    estimated_gate_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    estimated_area_percent: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_power_mw: Mapped[float | None] = mapped_column(Float, nullable=True)
    passes_constraint: Mapped[bool] = mapped_column(
        Boolean,
        Computed("estimated_area_percent < 5.0", persisted=True),
        nullable=False,
    )
    decision: Mapped[AuditDecision] = mapped_column(audit_decision_enum, nullable=False)
    auditor_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    audited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    agent_configuration: Mapped[AgentConfiguration | None] = relationship(back_populates="silicon_area_audits")
    simulation_run: Mapped[SimulationRun | None] = relationship(back_populates="silicon_area_audits")


class DeterminismCheck(Base):
    __tablename__ = "determinism_checks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    run_a_id: Mapped[UUID | None] = mapped_column(ForeignKey("simulation_runs.id"), nullable=True)
    run_b_id: Mapped[UUID | None] = mapped_column(ForeignKey("simulation_runs.id"), nullable=True)
    hashes_match: Mapped[bool] = mapped_column(Boolean, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Sprint(Base):
    __tablename__ = "sprints"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    project_id: Mapped[UUID | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    sprint_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[SprintStatus] = mapped_column(sprint_status_enum, nullable=False, server_default=text("'planned'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    project: Mapped[Project | None] = relationship(back_populates="sprints")
    user_stories: Mapped[list[UserStory]] = relationship(back_populates="sprint")


class UserStory(Base):
    __tablename__ = "user_stories"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    sprint_id: Mapped[UUID | None] = mapped_column(ForeignKey("sprints.id", ondelete="CASCADE"), nullable=True)
    epic_name: Mapped[str] = mapped_column(Text, nullable=False)
    persona: Mapped[str] = mapped_column(Text, nullable=False)
    story_text: Mapped[str] = mapped_column(Text, nullable=False)
    story_points: Mapped[int] = mapped_column(Integer, nullable=False)
    business_value: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[StoryStatus] = mapped_column(story_status_enum, nullable=False, server_default=text("'backlog'"))
    requirement_ids: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    sprint: Mapped[Sprint | None] = relationship(back_populates="user_stories")

    __table_args__ = (
        CheckConstraint("story_points BETWEEN 1 AND 5", name="user_stories_story_points_range"),
        CheckConstraint("business_value BETWEEN 1 AND 5", name="user_stories_business_value_range"),
    )


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    project_id: Mapped[UUID | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    requirement_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    subsystem: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[PriorityLevel] = mapped_column(priority_level_enum, nullable=False)
    priority_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    project: Mapped[Project | None] = relationship(back_populates="requirements")
    test_requirement_links: Mapped[list[TestRequirementLink]] = relationship(
        back_populates="requirement",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    project_id: Mapped[UUID | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    test_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    procedure: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    project: Mapped[Project | None] = relationship(back_populates="test_cases")
    test_requirement_links: Mapped[list[TestRequirementLink]] = relationship(
        back_populates="test_case",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TestRequirementLink(Base):
    __tablename__ = "test_requirement_links"

    test_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("test_cases.id", ondelete="CASCADE"),
        primary_key=True,
    )
    requirement_id: Mapped[UUID] = mapped_column(
        ForeignKey("requirements.id", ondelete="CASCADE"),
        primary_key=True,
    )

    test_case: Mapped[TestCase] = relationship(back_populates="test_requirement_links")
    requirement: Mapped[Requirement] = relationship(back_populates="test_requirement_links")
