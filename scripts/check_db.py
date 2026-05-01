from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def _read_env_value(env_path: Path, key: str) -> str | None:
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        if name.strip() == key:
            return value.strip()

    return None


def _ensure_sslmode(conn_url: str) -> str:
    if "sslmode=" in conn_url:
        return conn_url
    joiner = "&" if "?" in conn_url else "?"
    return f"{conn_url}{joiner}sslmode=require"


def _redact_url(conn_url: str) -> str:
    parts = urlsplit(conn_url)
    if not parts.hostname:
        return conn_url

    netloc = parts.hostname
    if parts.port:
        netloc = f"{netloc}:{parts.port}"
    if parts.username:
        netloc = f"{parts.username}:***@{netloc}"

    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check database connectivity.")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Path to an .env file containing DATABASE_URL.",
    )
    args = parser.parse_args()

    conn_url = os.getenv("DATABASE_URL")
    if not conn_url:
        conn_url = _read_env_value(args.env_file, "DATABASE_URL")

    if not conn_url:
        print("DATABASE_URL is not set in the environment or .env file.", file=sys.stderr)
        return 2

    try:
        import psycopg  # type: ignore
    except ModuleNotFoundError:
        print(
            "psycopg is not installed. Install with: pip install 'psycopg[binary]'",
            file=sys.stderr,
        )
        return 3

    conn_url = _ensure_sslmode(conn_url)
    redacted = _redact_url(conn_url)

    try:
        with psycopg.connect(conn_url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("select 1;")
                value = cur.fetchone()[0]
        print(f"Connection OK: {redacted} -> select 1 returned {value}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Connection failed: {redacted}\n{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
