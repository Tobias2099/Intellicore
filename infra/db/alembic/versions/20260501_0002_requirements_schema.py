"""Replace starter telemetry tables with requirements-driven schema.

Revision ID: 20260501_0002
Revises: 20260501_0001
Create Date: 2026-05-01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from intellicore_control.db.models import Base

revision = "20260501_0002"
down_revision = "20260501_0001"
branch_labels = None
depends_on = None

LEGACY_TABLES = (
    "area_audit_reports",
    "memory_trace_records",
    "telemetry_events",
    "simulation_runs",
)


def _has_legacy_simulation_runs() -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "simulation_runs" not in inspector.get_table_names(schema="public"):
        return False
    columns = {column["name"] for column in inspector.get_columns("simulation_runs", schema="public")}
    return {"config_name", "core_count", "deterministic_seed"}.issubset(columns)


def upgrade() -> None:
    bind = op.get_bind()

    if _has_legacy_simulation_runs():
        for table_name in LEGACY_TABLES:
            op.drop_table(table_name, if_exists=True)

    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, checkfirst=True)
