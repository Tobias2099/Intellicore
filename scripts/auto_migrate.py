from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


VERSIONS_DIR = Path("infra/db/alembic/versions")
DESTRUCTIVE_PATTERNS = (
    "drop_column",
    "drop_table",
    "drop_constraint",
    "drop_index",
    "execute",
)
RISKY_ALTER_PATTERN = re.compile(r"alter_column\s*\([^)]*(nullable\s*=\s*False|type_\s*=)", re.DOTALL)


def _run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"$ {' '.join(command)}")
    return subprocess.run(command, check=check, text=True)


def _latest_revision_file(before: set[Path]) -> Path | None:
    after = set(VERSIONS_DIR.glob("*.py"))
    generated = after - before
    if not generated:
        return None
    return max(generated, key=lambda path: path.stat().st_mtime)


def _upgrade_body(source: str) -> str:
    match = re.search(r"def upgrade\(\) -> None:\n(?P<body>.*?)(?=\n\ndef downgrade\(\) -> None:)", source, re.DOTALL)
    return match.group("body") if match else source


def _destructive_findings(revision_file: Path) -> list[str]:
    upgrade = _upgrade_body(revision_file.read_text(encoding="utf-8"))
    findings = [pattern for pattern in DESTRUCTIVE_PATTERNS if f"op.{pattern}" in upgrade]
    if RISKY_ALTER_PATTERN.search(upgrade):
        findings.append("risky alter_column")
    return findings


def _allow_destructive() -> bool:
    return os.environ.get("ALLOW_DESTRUCTIVE_MIGRATIONS", "").lower() in {"1", "true", "yes"}


def main() -> int:
    migration_message = os.environ.get("MIGRATION_MESSAGE", "schema change")

    _run(["alembic", "upgrade", "head"])

    check = subprocess.run(
        ["alembic", "check"],
        check=False,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        text=True,
    )
    print(check.stdout, end="")

    if check.returncode != 0:
        before = set(VERSIONS_DIR.glob("*.py"))
        _run(["alembic", "revision", "--autogenerate", "-m", migration_message])
        revision_file = _latest_revision_file(before)
        if revision_file is None:
            print("Alembic reported model drift but did not create a revision file.", file=sys.stderr)
            return 1

        findings = _destructive_findings(revision_file)
        if findings and not _allow_destructive():
            print(
                "\nDestructive or risky migration operations detected in "
                f"{revision_file}:\n- " + "\n- ".join(findings),
                file=sys.stderr,
            )
            print(
                "\nReview the generated migration before applying it. "
                "If this is intentional, rerun with ALLOW_DESTRUCTIVE_MIGRATIONS=true.",
                file=sys.stderr,
            )
            return 3

        _run(["alembic", "upgrade", "head"])
    else:
        print("No model changes detected; no migration revision generated.")

    _run([sys.executable, "scripts/check_db.py"])
    _run([sys.executable, "scripts/check_orm.py"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
