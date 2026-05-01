"""Initial IntelliCore telemetry schema.

Revision ID: 20260501_0001
Revises:
Create Date: 2026-05-01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260501_0001"
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names(schema="public")


def upgrade() -> None:
    if not _table_exists("simulation_runs"):
        op.create_table(
            "simulation_runs",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("config_name", sa.String(), nullable=False),
            sa.Column("isa", sa.String(), nullable=False),
            sa.Column("core_count", sa.Integer(), nullable=False),
            sa.Column("deterministic_seed", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint("core_count > 0", name="simulation_runs_core_count_positive"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _table_exists("telemetry_events"):
        op.create_table(
            "telemetry_events",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("run_id", sa.String(), nullable=False),
            sa.Column("cycle", sa.BigInteger(), nullable=False),
            sa.Column("core_id", sa.Integer(), nullable=False),
            sa.Column("cache_level", sa.String(), nullable=True),
            sa.Column("metric", sa.String(), nullable=False),
            sa.Column("value", sa.Float(), nullable=False),
            sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint("cycle >= 0", name="telemetry_events_cycle_non_negative"),
            sa.CheckConstraint("core_id >= 0", name="telemetry_events_core_id_non_negative"),
            sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    op.create_index(
        "telemetry_events_run_cycle_idx",
        "telemetry_events",
        ["run_id", "cycle"],
        unique=False,
        if_not_exists=True,
    )

    if not _table_exists("memory_trace_records"):
        op.create_table(
            "memory_trace_records",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("run_id", sa.String(), nullable=False),
            sa.Column("cycle", sa.BigInteger(), nullable=False),
            sa.Column("core_id", sa.Integer(), nullable=False),
            sa.Column("address", sa.String(), nullable=False),
            sa.Column("operation", sa.String(), nullable=False),
            sa.Column("cache_level", sa.String(), nullable=True),
            sa.Column("prefetch_outcome", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint("cycle >= 0", name="memory_trace_records_cycle_non_negative"),
            sa.CheckConstraint("core_id >= 0", name="memory_trace_records_core_id_non_negative"),
            sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    op.create_index(
        "memory_trace_run_core_cycle_idx",
        "memory_trace_records",
        ["run_id", "core_id", "cycle"],
        unique=False,
        if_not_exists=True,
    )

    if not _table_exists("area_audit_reports"):
        op.create_table(
            "area_audit_reports",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("run_id", sa.String(), nullable=False),
            sa.Column("agent_area_percent", sa.Float(), nullable=False),
            sa.Column("passes_budget", sa.Boolean(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint("agent_area_percent >= 0", name="area_audit_reports_area_non_negative"),
            sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    op.drop_table("area_audit_reports", if_exists=True)
    op.drop_index("memory_trace_run_core_cycle_idx", table_name="memory_trace_records", if_exists=True)
    op.drop_table("memory_trace_records", if_exists=True)
    op.drop_index("telemetry_events_run_cycle_idx", table_name="telemetry_events", if_exists=True)
    op.drop_table("telemetry_events", if_exists=True)
    op.drop_table("simulation_runs", if_exists=True)
