from __future__ import annotations

from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from intellicore_control.db.models import (
    AgentConfiguration,
    AuditDecision,
    CacheEventType,
    CacheLevel,
    CpuIsa,
    CpuMode,
    HardwareConfiguration,
    MemoryTrace,
    PerformanceReport,
    PrefetchOutcome,
    PriorityLevel,
    Project,
    Requirement,
    RewardSignal,
    SiliconAreaAudit,
    SimulationRun,
    Sprint,
    SprintStatus,
    StoryStatus,
    StrideType,
    TestCase,
    TestRequirementLink,
    UserStory,
)
from intellicore_control.db.url import database_url_with_ssl


SMOKE_PROJECT_NAME = "orm-smoke-check"


def main() -> int:
    engine = create_engine(database_url_with_ssl())

    with Session(engine) as session:
        stale_test_case = session.scalar(select(TestCase).where(TestCase.test_id == "ORM-SMOKE"))
        if stale_test_case is not None:
            session.delete(stale_test_case)

        stale_requirement = session.scalar(
            select(Requirement).where(Requirement.requirement_id == "ORM-SMOKE")
        )
        if stale_requirement is not None:
            session.delete(stale_requirement)

        existing = session.scalar(select(Project).where(Project.name == SMOKE_PROJECT_NAME))
        if existing is not None:
            session.delete(existing)

        session.commit()

        project = Project(name=SMOKE_PROJECT_NAME, description="Temporary ORM smoke project")
        session.add(project)
        session.flush()

        hardware = HardwareConfiguration(
            project_id=project.id,
            name="smoke-x86",
            isa=CpuIsa.X86,
            core_count=4,
            l1_size_kb=32,
            l2_size_kb=256,
            llc_size_kb=8192,
            l1_associativity=8,
            l2_associativity=8,
            llc_associativity=16,
            config_payload={"source": "orm-smoke"},
        )
        agent = AgentConfiguration(
            project_id=project.id,
            name="smoke-agent",
            learning_rate=0.0003,
            weight_matrix_kb=12.5,
            inference_cycles=2,
        )
        session.add_all([hardware, agent])
        session.flush()

        run = SimulationRun(
            project_id=project.id,
            hardware_config_id=hardware.id,
            agent_config_id=agent.id,
            is_baseline=False,
            cpu_mode=CpuMode.TIMING_SIMPLE,
            benchmark_name="synthetic-stride",
            random_seed=1,
            status="completed",
        )
        session.add(run)
        session.flush()

        session.add_all(
            [
                PerformanceReport(
                    simulation_run_id=run.id,
                    final_ipc=1.2,
                    final_mpki=4.5,
                    amal_cycles=22.0,
                    prefetcher_accuracy=0.75,
                ),
                MemoryTrace(
                    simulation_run_id=run.id,
                    cycle_timestamp=10,
                    core_id=0,
                    cache_level=CacheLevel.L1,
                    memory_address=0x1000,
                    event_type=CacheEventType.PREFETCH_FILL,
                    stride_type=StrideType.CONSTANT,
                    prefetch_outcome=PrefetchOutcome.USEFUL,
                ),
                RewardSignal(
                    simulation_run_id=run.id,
                    agent_id=0,
                    cycle_timestamp=10,
                    reward_value=1.0,
                    action_taken="prefetch",
                    target_address=0x1040,
                ),
                SiliconAreaAudit(
                    agent_config_id=agent.id,
                    simulation_run_id=run.id,
                    estimated_gate_count=1000,
                    estimated_area_percent=1.5,
                    decision=AuditDecision.APPROVED,
                ),
            ]
        )

        sprint = Sprint(
            project_id=project.id,
            sprint_number=1,
            name="Simulation Foundation",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 31),
            status=SprintStatus.PLANNED,
        )
        requirement = Requirement(
            project_id=project.id,
            requirement_id="ORM-SMOKE",
            category="functional",
            subsystem="ACM",
            name="ORM smoke requirement",
            description="Verifies ORM mapping for requirements storage.",
            priority=PriorityLevel.MUST_HAVE,
        )
        test_case = TestCase(
            project_id=project.id,
            test_id="ORM-SMOKE",
            name="ORM smoke test",
            description="Verifies SQLAlchemy can persist the requirements-driven schema.",
        )
        session.add_all([sprint, requirement, test_case])
        session.flush()

        session.add_all(
            [
                UserStory(
                    sprint_id=sprint.id,
                    epic_name="Tooling",
                    persona="Developer",
                    story_text="As a developer, I want ORM smoke coverage.",
                    story_points=1,
                    business_value=1,
                    status=StoryStatus.BACKLOG,
                    requirement_ids=["ORM-SMOKE"],
                ),
                TestRequirementLink(test_case_id=test_case.id, requirement_id=requirement.id),
            ]
        )
        session.commit()

        persisted = session.scalar(select(Project).where(Project.name == SMOKE_PROJECT_NAME))
        if persisted is None:
            raise RuntimeError("ORM smoke project was not persisted.")

        session.delete(persisted)
        session.commit()

    print("ORM smoke check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
