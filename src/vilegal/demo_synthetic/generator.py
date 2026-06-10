from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .schema import DEFAULT_DISCLAIMER, SyntheticDemoRow, row_id_from_index


@dataclass(frozen=True)
class TrackASyntheticConfig:
    track: str
    name: str
    mode: str
    safety: dict[str, object]
    generation: dict[str, object]
    metadata: dict[str, object]


@dataclass(frozen=True)
class TemplatePrompt:
    task_type: str
    difficulty: str
    instruction: str
    input_template: str
    output_template: str


TEMPLATE_LIBRARY = (
    TemplatePrompt(
        task_type="classification",
        difficulty="easy",
        instruction="Classify the fictional compliance request into a demo category.",
        input_template="Scenario {index}: A fictional neighborhood cafe updates its opening hours and wants to know which internal admin checklist bucket fits the request.",
        output_template="Demo classification: public-notice-admin-task. This is a synthetic portfolio example for workflow mechanics only, not legal advice.",
    ),
    TemplatePrompt(
        task_type="explanation",
        difficulty="medium",
        instruction="Explain the synthetic next step in plain language for the fictional business owner.",
        input_template="Scenario {index}: A fictional online shop asks what kind of demo evidence it should gather before filing a pretend consumer-response memo.",
        output_template="Suggested demo explanation: gather receipts, timestamps, and a short summary of the issue for a fictional internal review note. This remains synthetic-demo guidance only.",
    ),
    TemplatePrompt(
        task_type="retrieval_style_qa",
        difficulty="easy",
        instruction="Answer the synthetic retrieval-style question using only the fictional policy note.",
        input_template="Scenario {index}: Fictional policy note says every demo record should keep an owner name, issue date, and follow-up status. Which field should be checked first when the date is missing?",
        output_template="Demo answer: check the issue-date field first because the fictional note explicitly lists it as required metadata. This is a synthetic retrieval-style example, not official legal text.",
    ),
    TemplatePrompt(
        task_type="drafting_demo",
        difficulty="medium",
        instruction="Draft a short synthetic response memo for the fictional requester.",
        input_template="Scenario {index}: A fictional startup wants a one-paragraph memo about renewing a pretend operating notice with a district office.",
        output_template="Synthetic memo: confirm the fictional notice identifier, record the requested renewal date, and route the request to the demo compliance queue for manual follow-up. This memo is not legal advice.",
    ),
    TemplatePrompt(
        task_type="classification",
        difficulty="medium",
        instruction="Choose the best synthetic label for the fictional paperwork issue.",
        input_template="Scenario {index}: A fictional household business forgot to archive a mock invoice acknowledgment and needs a portfolio-demo label.",
        output_template="Demo classification: record-keeping-gap. The label is synthetic and meant only to demonstrate dataset structure.",
    ),
    TemplatePrompt(
        task_type="explanation",
        difficulty="hard",
        instruction="Explain the fictional trade-off between speed and review quality in this synthetic compliance workflow.",
        input_template="Scenario {index}: A fictional team wants to answer all mock citizen questions immediately without a manual review checkpoint.",
        output_template="Synthetic explanation: faster responses reduce review time, but the demo workflow should still include a human check before any outward-facing reply. This is a safety-oriented synthetic example.",
    ),
    TemplatePrompt(
        task_type="retrieval_style_qa",
        difficulty="medium",
        instruction="Find the key fact from the fictional note and answer the synthetic question.",
        input_template="Scenario {index}: Fictional note says a demo complaint bundle should include a summary, attachment list, and internal reviewer name. Which item identifies the responsible reviewer?",
        output_template="Demo answer: the internal reviewer name identifies responsibility in the fictional note. This answer is synthetic-demo only.",
    ),
    TemplatePrompt(
        task_type="drafting_demo",
        difficulty="hard",
        instruction="Draft a synthetic checklist item for a fictional licensing follow-up.",
        input_template="Scenario {index}: A fictional logistics firm needs a short checklist line before submitting a pretend warehouse update request.",
        output_template="Synthetic checklist line: verify the fictional warehouse code, confirm the mock address change, and attach the internal routing reference before submission. Not legal advice.",
    ),
)


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


def load_track_a_config(path: str | Path) -> TrackASyntheticConfig:
    source = Path(path)
    payload: dict[str, object] = {}
    current_mapping: dict[str, object] | None = None

    for raw_line in source.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        if indent == 0:
            current_mapping = None
            key, _, remainder = line.partition(":")
            if not _:
                raise ValueError(f"Invalid top-level config line: {raw_line}")
            value = remainder.strip()
            if value:
                payload[key] = _parse_scalar(value)
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

        raise ValueError(f"Unsupported config structure: {raw_line}")

    return TrackASyntheticConfig(
        track=str(payload["track"]),
        name=str(payload["name"]),
        mode=str(payload["mode"]),
        safety=dict(payload["safety"]),
        generation=dict(payload["generation"]),
        metadata=dict(payload["metadata"]),
    )


def generate_synthetic_demo_rows(count: int, *, disclaimer: str = DEFAULT_DISCLAIMER) -> list[SyntheticDemoRow]:
    if count <= 0:
        raise ValueError("count must be greater than zero.")

    rows: list[SyntheticDemoRow] = []
    for index in range(1, count + 1):
        template = TEMPLATE_LIBRARY[(index - 1) % len(TEMPLATE_LIBRARY)]
        rows.append(
            SyntheticDemoRow(
                id=row_id_from_index(index),
                instruction=template.instruction,
                input=template.input_template.format(index=index),
                output=template.output_template,
                task_type=template.task_type,
                difficulty=template.difficulty,
                disclaimer=disclaimer,
            )
        )
    return rows


def write_jsonl(path: str | Path, rows: Iterable[SyntheticDemoRow]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")
    return output_path
