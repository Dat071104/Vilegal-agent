from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .schema import (
    ALLOWED_DIFFICULTIES,
    ALLOWED_TASK_TYPES,
    DEFAULT_DOMAIN,
    DEFAULT_FORMAT,
    DEFAULT_SOURCE,
    REQUIRED_FIELDS,
)

DISCLAIMER_TERMS = ("synthetic", "demo", "not legal advice")
POSITIVE_AUTHORITY_CLAIMS = (
    "this is official legal text",
    "this is official legal advice",
    "official legal authority",
    "official legal answer",
    "binding legal advice",
    "authoritative legal interpretation",
)


@dataclass(frozen=True)
class ValidationIssue:
    line_number: int
    errors: tuple[str, ...]


@dataclass(frozen=True)
class ValidationSummary:
    total_rows: int
    valid_rows: int
    invalid_rows: int
    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)


def _read_text(value: object, *, field_name: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    text = value.strip()
    if not text and not allow_empty:
        raise ValueError(f"{field_name} must not be blank.")
    return text


def _contains_positive_authority_claim(text: str) -> bool:
    normalized = text.lower()
    return any(pattern in normalized for pattern in POSITIVE_AUTHORITY_CLAIMS)


def validate_demo_row(payload: dict[str, object]) -> list[str]:
    errors: list[str] = []

    for field_name in REQUIRED_FIELDS:
        if field_name not in payload:
            errors.append(f"Missing required field: {field_name}")

    if errors:
        return errors

    try:
        row_id = _read_text(payload["id"], field_name="id")
        instruction = _read_text(payload["instruction"], field_name="instruction")
        row_input = _read_text(payload["input"], field_name="input", allow_empty=True)
        output = _read_text(payload["output"], field_name="output")
        source = _read_text(payload["source"], field_name="source")
        row_format = _read_text(payload["format"], field_name="format")
        domain = _read_text(payload["domain"], field_name="domain")
        task_type = _read_text(payload["task_type"], field_name="task_type")
        difficulty = _read_text(payload["difficulty"], field_name="difficulty")
        disclaimer = _read_text(payload["disclaimer"], field_name="disclaimer")
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    if not row_id.startswith("synthetic-demo-"):
        errors.append("id must start with synthetic-demo-.")
    if source != DEFAULT_SOURCE:
        errors.append("source must equal synthetic-demo.")
    if row_format != DEFAULT_FORMAT:
        errors.append("format must equal alpaca.")
    if domain != DEFAULT_DOMAIN:
        errors.append("domain must equal vietnamese-legal-demo.")
    if task_type not in ALLOWED_TASK_TYPES:
        errors.append(f"task_type is invalid: {task_type}")
    if difficulty not in ALLOWED_DIFFICULTIES:
        errors.append(f"difficulty is invalid: {difficulty}")

    if payload["is_synthetic"] is not True:
        errors.append("is_synthetic must be true.")
    if payload["is_legal_ground_truth"] is not False:
        errors.append("is_legal_ground_truth must be false.")
    if payload["approved_for_rag_index"] is not False:
        errors.append("approved_for_rag_index must be false.")

    disclaimer_normalized = disclaimer.lower()
    for term in DISCLAIMER_TERMS:
        if term not in disclaimer_normalized:
            errors.append(f"disclaimer must mention: {term}")

    combined_text = " ".join((instruction, row_input, output))
    if _contains_positive_authority_claim(combined_text):
        errors.append("Row must not claim official legal authority.")

    return errors


def validate_jsonl_file(path: str | Path) -> ValidationSummary:
    source = Path(path)
    total_rows = 0
    valid_rows = 0
    issues: list[ValidationIssue] = []

    with source.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            total_rows += 1
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                issues.append(ValidationIssue(line_number=line_number, errors=(f"Invalid JSON: {exc.msg}",)))
                continue

            if not isinstance(payload, dict):
                issues.append(ValidationIssue(line_number=line_number, errors=("Row must be a JSON object.",)))
                continue

            errors = validate_demo_row(payload)
            if errors:
                issues.append(ValidationIssue(line_number=line_number, errors=tuple(errors)))
                continue

            valid_rows += 1

    return ValidationSummary(
        total_rows=total_rows,
        valid_rows=valid_rows,
        invalid_rows=len(issues),
        issues=tuple(issues),
    )
