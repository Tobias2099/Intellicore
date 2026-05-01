from __future__ import annotations

from pathlib import Path
from typing import Any


def load_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        return _load_yaml_subset(text)

    return yaml.safe_load(text)


def _load_yaml_subset(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any, dict[str, Any] | None, str | None]] = [(-1, root, None, None)]

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()

        current_indent, current, parent, parent_key = stack[-1]

        if line.startswith("- "):
            if not isinstance(current, list):
                if parent is None or parent_key is None:
                    raise ValueError("List item has no parent key")
                replacement: list[Any] = []
                parent[parent_key] = replacement
                current = replacement
                stack[-1] = (current_indent, current, parent, parent_key)
            current.append(_parse_scalar(line[2:].strip()))
            continue

        key, _, value = line.partition(":")
        if not key or not isinstance(current, dict):
            raise ValueError(f"Unsupported config line: {raw_line}")

        if value.strip():
            current[key] = _parse_scalar(value.strip())
        else:
            child: dict[str, Any] = {}
            current[key] = child
            stack.append((indent, child, current, key))

    return root


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value.strip('"')
