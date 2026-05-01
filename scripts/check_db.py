from __future__ import annotations

import os
import sys
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import psycopg


REQUIRED_TABLES = {
    "agent_configurations",
    "coordination_events",
    "determinism_checks",
    "hardware_configurations",
    "memory_traces",
    "performance_reports",
    "projects",
    "requirements",
    "reward_signals",
    "silicon_area_audits",
    "simulation_runs",
    "sprints",
    "test_cases",
    "test_requirement_links",
    "user_stories",
}


def _connection_url() -> str | None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return None

    parsed = urlparse(database_url)
    query = dict(parse_qsl(parsed.query))
    query.setdefault("sslmode", "require")
    return urlunparse(parsed._replace(query=urlencode(query)))


def main() -> int:
    database_url = _connection_url()
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
