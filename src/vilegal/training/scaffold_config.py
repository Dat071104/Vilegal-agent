from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Phase3AScaffoldConfig:
    phase: str
    name: str
    mode: str
    safety: dict[str, object]
    data: dict[str, object]
    training: dict[str, object]
    blocked_until_future_gate: list[str]


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _parse_scalar(value: str) -> object:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    if value.isdigit():
        return int(value)
    return _strip_quotes(value)


def load_phase3a_scaffold_config(path: str | Path) -> Phase3AScaffoldConfig:
    source = Path(path)
    lines = source.read_text(encoding="utf-8").splitlines()

    payload: dict[str, object] = {}
    current_mapping: dict[str, object] | None = None
    current_list: list[object] | None = None

    for raw_line in lines:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        if indent == 0:
            current_mapping = None
            current_list = None
            key, _, remainder = line.partition(":")
            if not _:
                raise ValueError(f"Invalid top-level config line: {raw_line}")
            value = remainder.strip()
            if value:
                payload[key] = _parse_scalar(value)
            else:
                if key == "blocked_until_future_gate":
                    payload[key] = []
                    current_list = payload[key]
                else:
                    payload[key] = {}
                    current_mapping = payload[key]
            continue

        if indent == 2 and current_mapping is not None:
            key, _, remainder = line.partition(":")
            if not _:
                raise ValueError(f"Invalid mapping line: {raw_line}")
            current_mapping[key] = _parse_scalar(remainder.strip())
            continue

        if indent == 2 and current_list is not None and line.startswith("- "):
            current_list.append(_parse_scalar(line[2:].strip()))
            continue

        raise ValueError(f"Unsupported scaffold config structure: {raw_line}")

    return Phase3AScaffoldConfig(
        phase=str(payload["phase"]),
        name=str(payload["name"]),
        mode=str(payload["mode"]),
        safety=dict(payload["safety"]),
        data=dict(payload["data"]),
        training=dict(payload["training"]),
        blocked_until_future_gate=list(payload["blocked_until_future_gate"]),
    )
