#!/usr/bin/env python3
"""Print a compact summary from gem5 stats.txt files."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path


STAT_LINE = re.compile(r"^(?P<name>\S+)\s+(?P<value>[-+a-zA-Z0-9.]+)")


def parse_stats(path: Path) -> dict[str, float]:
    stats: dict[str, float] = {}

    with path.open(encoding="utf-8") as stats_file:
        for line in stats_file:
            match = STAT_LINE.match(line.strip())
            if not match:
                continue

            name = match.group("name")
            raw_value = match.group("value")
            try:
                value = float(raw_value)
            except ValueError:
                continue

            if math.isfinite(value):
                stats[name] = value

    return stats


def benchmark_name(path: Path) -> str:
    if path.name == "stats.txt" and path.parent.name:
        return path.parent.name
    return path.stem


def average_matching(stats: dict[str, float], pattern: str) -> float | None:
    regex = re.compile(pattern)
    values = [value for key, value in stats.items() if regex.fullmatch(key)]
    if not values:
        return None
    return sum(values) / len(values)


def per_core_matching(stats: dict[str, float], pattern: str) -> list[tuple[int, float]]:
    regex = re.compile(pattern)
    matches: list[tuple[int, float]] = []
    for key, value in stats.items():
        match = regex.fullmatch(key)
        if match:
            matches.append((int(match.group("core")), value))
    return sorted(matches)


def metric(stats: dict[str, float], *names: str) -> float | None:
    for name in names:
        if name in stats:
            return stats[name]
    return None


def format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def format_decimal(value: float | None, digits: int = 6) -> str:
    if value is None:
        return "n/a"
    text = f"{value:.{digits}f}"
    return text.rstrip("0").rstrip(".")


def format_count(value: float) -> str:
    return f"{int(value):,}" if value.is_integer() else format_decimal(value)


def format_per_core(values: list[tuple[int, float]]) -> str:
    if not values:
        return "n/a"
    return ", ".join(f"cpu{core}={format_count(value)}" for core, value in values)


def summarize(path: Path) -> str:
    stats = parse_stats(path)

    l1d_miss_rate = average_matching(
        stats,
        r"system\.cpu\d+\.dcache\.overallMissRate::total",
    )
    l2_miss_rate = metric(
        stats,
        "system.l2cache.overallMissRate::total",
        "system.l2.overallMissRate::total",
    )
    l1d_misses_by_core = per_core_matching(
        stats,
        r"system\.cpu(?P<core>\d+)\.dcache\.overallMisses::total",
    )
    ipc = average_matching(stats, r"system\.cpu\d+\.ipc")

    lines = [
        f"Benchmark: {benchmark_name(path)}",
        f"L1D miss rate: {format_percent(l1d_miss_rate)}",
        f"L1D misses/core: {format_per_core(l1d_misses_by_core)}",
        f"L2 miss rate: {format_percent(l2_miss_rate)}",
        f"IPC: {format_decimal(ipc, 3)}",
        f"Sim seconds: {format_decimal(metric(stats, 'simSeconds'), 6)}",
    ]
    return "\n".join(lines)


def default_stats_files(root: Path) -> list[Path]:
    return sorted(root.glob("m5out/*/stats.txt"))


def stats_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.append(path / "stats.txt")
        else:
            files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize important gem5 stats.txt metrics.",
    )
    parser.add_argument(
        "stats_files",
        nargs="*",
        type=Path,
        help="stats.txt file(s) or run directories to summarize. Defaults to m5out/*/stats.txt.",
    )
    args = parser.parse_args()

    paths = stats_files(args.stats_files) if args.stats_files else default_stats_files(Path.cwd())
    if not paths:
        parser.error("no stats files found; pass one or run from the repo root")

    for index, path in enumerate(paths):
        if index:
            print()
        print(summarize(path))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
