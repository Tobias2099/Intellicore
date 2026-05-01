from __future__ import annotations

import os
import sys

import psycopg


REQUIRED_TABLES = {
    "area_audit_reports",
    "memory_trace_records",
    "simulation_runs",
    "telemetry_events",
}


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL must be set to the Supabase Postgres connection string.", file=sys.stderr)
        return 2

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )
            tables = {row[0] for row in cursor.fetchall()}

    missing = REQUIRED_TABLES - tables
    if missing:
        print(f"Missing required tables: {sorted(missing)}", file=sys.stderr)
        return 1

    print("Database schema check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
