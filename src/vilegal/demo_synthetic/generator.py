from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .schema import ALLOWED_DIFFICULTIES, ALLOWED_TASK_TYPES, DEFAULT_DISCLAIMER, SyntheticDemoRow, row_id_from_index


@dataclass(frozen=True)
class TrackASyntheticConfig:
    track: str
    name: str
    mode: str
    safety: dict[str, object]
    generation: dict[str, object]
    metadata: dict[str, object]
    audit: dict[str, object]
    split: dict[str, object]


@dataclass(frozen=True)
class TopicProfile:
    topic: str
    workflow_label: str
    record_name: str
    focus_field: str
    action_step: str
    caution: str


TOPIC_PROFILES = (
    TopicProfile("business registration update", "profile-update-routing", "portfolio profile update note", "registration reference", "record the fictional change request", "keep the response framed as a demo workflow"),
    TopicProfile("consumer complaint intake", "complaint-intake-review", "mock complaint intake sheet", "issue summary", "log the fictional complaint owner and timeline", "avoid presenting the answer as a legal ruling"),
    TopicProfile("permit extension reminder", "permit-extension-prep", "synthetic permit extension checklist", "renewal due date", "prepare a fictional renewal checklist", "state that the item is not official legal text"),
    TopicProfile("warehouse safety notice", "facility-safety-review", "fictional warehouse review memo", "site code", "capture the pretend safety follow-up items", "treat the output as demo content only"),
    TopicProfile("vendor invoice mismatch", "billing-variance-review", "demo billing discrepancy note", "invoice reference", "summarize the fictional mismatch facts", "avoid authoritative legal language"),
    TopicProfile("training certificate renewal", "credential-renewal-routing", "synthetic renewal tracker", "certificate expiry date", "route the fictional renewal packet to a demo queue", "remind the reader that this is not legal advice"),
    TopicProfile("branch address correction", "branch-address-correction", "fictional branch change form", "branch identifier", "collect the pretend address delta", "preserve the synthetic-demo label"),
    TopicProfile("product labeling review", "labeling-quality-check", "demo labeling review card", "label version", "note the fictional packaging concern", "keep the tone non-authoritative"),
    TopicProfile("tax reminder planning", "deadline-monitor", "synthetic deadline reminder", "reporting month", "track the fictional reminder date", "do not imply official government instruction"),
    TopicProfile("procurement archive cleanup", "procurement-record-audit", "fictional archive inventory", "archive batch name", "list the pretend archive gaps", "keep the answer portfolio-focused"),
    TopicProfile("data privacy contact update", "privacy-contact-update", "demo privacy contact brief", "contact owner", "document the fictional contact change", "say explicitly that the content is synthetic"),
    TopicProfile("cooperative membership notice", "membership-notice-routing", "synthetic cooperative notice memo", "membership period", "capture the fictional notice status", "avoid legal-ground-truth framing"),
)

ACTORS = (
    "fictional cafe owner",
    "fictional logistics manager",
    "fictional training-center coordinator",
    "fictional online shop operator",
    "fictional warehouse supervisor",
    "fictional branch administrator",
    "fictional procurement assistant",
    "fictional cooperative officer",
)

LOCATIONS = (
    "District 1",
    "Thu Duc City",
    "Da Nang demo office",
    "Can Tho demo branch",
    "Hai Phong portfolio site",
    "Hue synthetic service desk",
)

CHANNELS = (
    "internal admin queue",
    "demo operations inbox",
    "portfolio compliance board",
    "synthetic reviewer checklist",
    "mock service desk handoff",
)

TRIGGERS = (
    "a contact detail changed yesterday",
    "a mock filing deadline is coming next week",
    "a synthetic reviewer found missing metadata",
    "a fictional stakeholder requested a status summary",
    "a demo checklist item was left unresolved",
    "a pretend support ticket was reopened",
)

CLASSIFICATION_INSTRUCTIONS = (
    "Assign the best synthetic workflow label for case {case_anchor}: a fictional {topic} request raised by a {actor} in {location}.",
    "Choose the most appropriate portfolio-demo category for case {case_anchor}, a fictional {topic} scenario involving a {actor} and the {channel}.",
    "Map case {case_anchor}, a fictional {topic} issue, to the clearest internal demo queue after {trigger}.",
    "Label synthetic case {case_anchor} with the best portfolio routing tag for the {record_name}.",
)

EXPLANATION_INSTRUCTIONS = (
    "Explain the next synthetic workflow step for case {case_anchor}, a fictional {topic} request, in plain language for a {actor} in {location}.",
    "Write a short synthetic explanation for case {case_anchor} that helps a {actor} understand the fictional {topic} follow-up through the {channel}.",
    "Describe the safest demo-only next step for case {case_anchor}, a fictional {topic} scenario after {trigger}.",
    "Summarize the portfolio-demo reasoning for case {case_anchor}, a fictional {topic} review path tied to the {record_name}.",
)

RETRIEVAL_INSTRUCTIONS = (
    "Answer the synthetic retrieval-style question for case {case_anchor} using only the fictional note in the prompt for the {topic} case in {location}.",
    "Find the key fact from the fictional memo and answer case {case_anchor}, a demo-only {topic} question raised by a {actor}.",
    "Use the synthetic policy note to answer case {case_anchor}, a fictional {topic} lookup question routed through the {channel}.",
    "Identify the relevant detail in case {case_anchor}, the fictional record, and provide the synthetic answer after {trigger}.",
)

DRAFTING_INSTRUCTIONS = (
    "Draft a short synthetic response memo for case {case_anchor}, a fictional {topic} request in {location}.",
    "Write a compact portfolio-demo checklist line for case {case_anchor}, a fictional {topic} follow-up handled by the {channel}.",
    "Prepare a one-paragraph synthetic note for case {case_anchor}, a fictional {topic} update after {trigger}.",
    "Draft a demo-only routing message for case {case_anchor}, a fictional {topic} scenario tied to the {record_name}.",
)

INPUT_STYLES = (
    "Scenario {index}: A {actor} in {location} is preparing a {record_name} after {trigger}. The team needs help with a fictional {topic} item and wants to know how to handle the {focus_field}.",
    "Scenario {index}: During a review in {location}, a {actor} asks the {channel} how to process a synthetic {topic} case. The current record is a {record_name}, and the most important field is the {focus_field}.",
    "Scenario {index}: A portfolio-demo workflow in {location} receives a fictional {topic} request from a {actor}. The mock packet references a {record_name} and highlights the {focus_field} after {trigger}.",
    "Scenario {index}: The {channel} receives a synthetic {topic} question from a {actor}. The fictional case comes from {location}, uses a {record_name}, and needs attention on the {focus_field}.",
)

CLASSIFICATION_OUTPUTS = (
    "Synthetic label for {case_anchor}: {workflow_label}. Reason: the fictional scenario in {location} centers on the {focus_field}, so the demo workflow should {action_step}. This is synthetic demo content only, not legal advice.",
    "Demo classification for {case_anchor}: {workflow_label}. The fictional {topic} request from the {actor} should move through the {channel} queue that starts by {action_step}. This answer is not official legal text.",
    "Portfolio-demo routing tag for {case_anchor}: {workflow_label}. The safest synthetic choice is to {action_step} before any outward-facing reply on the {record_name}. This remains a non-authoritative example.",
)

EXPLANATION_OUTPUTS = (
    "Synthetic explanation for {case_anchor}: start by {action_step}, then verify the {focus_field} in the {record_name} for the {actor} in {location}. {caution}, and keep the response clearly framed as synthetic-demo guidance only.",
    "Demo guidance for {case_anchor}: the fictional team should first {action_step} because the prompt highlights the {focus_field} and routes work through the {channel}. {caution}. This is not legal advice.",
    "Portfolio explanation for {case_anchor}: review the {record_name}, confirm the {focus_field}, and {action_step} after {trigger}. The response stays synthetic-only and does not claim legal authority.",
)

RETRIEVAL_OUTPUTS = (
    "Demo answer for {case_anchor}: the key fact is the {focus_field}, because the fictional note for the {topic} case in {location} points to it before the team should {action_step}. This is synthetic-demo output only, not official legal text.",
    "Synthetic retrieval answer for {case_anchor}: check the {focus_field} first, then {action_step} through the {channel}. The example is portfolio content and must not be treated as legal advice.",
    "Portfolio-demo answer for {case_anchor}: the fictional record emphasizes the {focus_field}; that is the detail the reviewer for the {record_name} should use before they {action_step}. This is not authoritative legal guidance.",
)

DRAFTING_OUTPUTS = (
    "Synthetic memo for {case_anchor}: confirm the {focus_field}, {action_step}, and send the {record_name} through the {channel} for the {actor} in {location}. This note is synthetic demo data only and not legal advice.",
    "Demo draft for {case_anchor}: acknowledge the fictional {topic} request, confirm the {focus_field}, and {action_step} after {trigger}. The wording is portfolio-only and not official legal text.",
    "Portfolio-demo note for {case_anchor}: route the fictional case to the {channel}, verify the {focus_field}, and {action_step} for the {record_name}. This remains a synthetic example only.",
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
        audit=dict(payload["audit"]),
        split=dict(payload["split"]),
    )


def _select(values: tuple[str, ...] | tuple[TopicProfile, ...], index: int, *, stride: int = 1):
    return values[((index - 1) * stride) % len(values)]


def _difficulty_for_index(index: int) -> str:
    return ALLOWED_DIFFICULTIES[(index - 1) % len(ALLOWED_DIFFICULTIES)]


def _task_type_for_index(index: int) -> str:
    return ALLOWED_TASK_TYPES[(index - 1) % len(ALLOWED_TASK_TYPES)]


def _instruction_template(task_type: str, index: int) -> str:
    mapping = {
        "classification": CLASSIFICATION_INSTRUCTIONS,
        "explanation": EXPLANATION_INSTRUCTIONS,
        "retrieval_style_qa": RETRIEVAL_INSTRUCTIONS,
        "drafting_demo": DRAFTING_INSTRUCTIONS,
    }
    templates = mapping[task_type]
    return templates[((index - 1) // len(ALLOWED_TASK_TYPES)) % len(templates)]


def _output_template(task_type: str, index: int) -> str:
    mapping = {
        "classification": CLASSIFICATION_OUTPUTS,
        "explanation": EXPLANATION_OUTPUTS,
        "retrieval_style_qa": RETRIEVAL_OUTPUTS,
        "drafting_demo": DRAFTING_OUTPUTS,
    }
    templates = mapping[task_type]
    return templates[((index - 1) // len(ALLOWED_DIFFICULTIES)) % len(templates)]


def _render_row(index: int, *, disclaimer: str) -> SyntheticDemoRow:
    task_type = _task_type_for_index(index)
    difficulty = _difficulty_for_index(index)
    profile = _select(TOPIC_PROFILES, index, stride=5)
    actor = _select(ACTORS, index, stride=7)
    location = _select(LOCATIONS, index, stride=11)
    channel = _select(CHANNELS, index, stride=13)
    trigger = _select(TRIGGERS, index, stride=17)
    input_template = INPUT_STYLES[((index - 1) // 3) % len(INPUT_STYLES)]
    instruction_template = _instruction_template(task_type, index)
    output_template = _output_template(task_type, index)

    context = {
        "index": index,
        "case_anchor": row_id_from_index(index),
        "topic": profile.topic,
        "workflow_label": profile.workflow_label,
        "record_name": profile.record_name,
        "focus_field": profile.focus_field,
        "action_step": profile.action_step,
        "caution": profile.caution,
        "actor": actor,
        "location": location,
        "channel": channel,
        "trigger": trigger,
        "difficulty": difficulty,
    }

    return SyntheticDemoRow(
        id=row_id_from_index(index),
        instruction=instruction_template.format(**context),
        input=input_template.format(**context),
        output=output_template.format(**context),
        task_type=task_type,
        difficulty=difficulty,
        disclaimer=disclaimer,
    )


def generate_synthetic_demo_rows(count: int, *, disclaimer: str = DEFAULT_DISCLAIMER) -> list[SyntheticDemoRow]:
    if count <= 0:
        raise ValueError("count must be greater than zero.")

    return [_render_row(index, disclaimer=disclaimer) for index in range(1, count + 1)]


def write_jsonl(path: str | Path, rows: Iterable[SyntheticDemoRow]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")
    return output_path
