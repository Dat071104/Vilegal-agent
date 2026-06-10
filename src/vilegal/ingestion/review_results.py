"""
review_results.py - Phase 2I human-review result validation and adjudication.

Validates reviewer decisions exported from the Phase 2H
reviewer_decision_template.csv workflow. This module never promotes any
candidate to legal ground truth and never approves any candidate for RAG
indexing during Phase 2I.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

PHASE_NAME = "Phase 2I - Human Review Results Schema + Adjudication Workflow"
REVIEW_RESULTS_VERSION = "phase_2i_v1"

ACCEPTED_DECISION_LABELS = (
    "accept_for_later_corpus_candidate",
    "reject_not_article",
    "reject_duplicate",
    "reject_too_short",
    "reject_too_long",
    "reject_missing_metadata",
    "needs_legal_expert_review",
    "needs_parser_fix",
    "uncertain",
)

ACCEPTED_CONFIDENCE_VALUES = ("high", "medium", "low")

REQUIRED_REVIEW_RESULT_FIELDS = (
    "reviewer_id",
    "review_date",
    "candidate_id",
    "decision_label",
    "confidence",
    "notes",
    "legal_ground_truth_approved",
    "rag_index_approved",
)

PRIORITY_DECISION_LABELS = (
    "needs_parser_fix",
    "needs_legal_expert_review",
    "uncertain",
)

FALSE_VALUES = {"false", "0", "no", "n"}
TRUE_VALUES = {"true", "1", "yes", "y"}


@dataclass
class InvalidReviewRow:
    row_number: int
    candidate_id: str
    reasons: list[str]


@dataclass
class CandidateAdjudication:
    candidate_id: str
    review_count: int
    reviewer_ids: list[str]
    decision_labels: list[str]
    confidence_values: list[str]
    adjudication_status: str
    consensus_label: str | None = None


@dataclass
class ReviewResultsReport:
    phase: str
    review_results_version: str
    review_file: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    decision_counts: dict[str, int]
    confidence_counts: dict[str, int]
    adjudication_counts: dict[str, int]
    distinct_candidate_ids: int
    distinct_reviewers: int
    approved_for_rag_index_true_count: int
    legal_ground_truth_approved_true_count: int
    invalid_row_details: list[InvalidReviewRow] = field(default_factory=list)
    adjudication_results: list[CandidateAdjudication] = field(default_factory=list)
    safety_verdict: str = "FAIL"


def load_review_results_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def parse_false_only_flag(field_name: str, raw_value: Any) -> tuple[bool | None, str | None]:
    value = normalize_text(raw_value).lower()
    if not value:
        return None, f"{field_name} is required."
    if value in FALSE_VALUES:
        return False, None
    if value in TRUE_VALUES:
        return True, f"{field_name} must remain false in Phase 2I."
    return None, f"{field_name} must be a boolean false value."


def validate_review_date(raw_value: Any) -> tuple[str | None, str | None]:
    value = normalize_text(raw_value)
    if not value:
        return None, "review_date is required."
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None, "review_date must be ISO format YYYY-MM-DD."
    return parsed.isoformat(), None


def validate_required_fields(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for field_name in REQUIRED_REVIEW_RESULT_FIELDS:
        if not normalize_text(row.get(field_name)):
            reasons.append(f"{field_name} is required.")
    return reasons


def validate_review_row(row: dict[str, Any], row_number: int) -> tuple[dict[str, Any] | None, InvalidReviewRow | None]:
    normalized = {key: normalize_text(value) for key, value in row.items()}
    reasons = validate_required_fields(normalized)

    review_date, review_date_error = validate_review_date(normalized.get("review_date"))
    if review_date_error:
        reasons.append(review_date_error)

    candidate_id = normalize_text(normalized.get("candidate_id"))
    if not candidate_id:
        reasons.append("candidate_id is required.")

    decision_label = normalize_text(normalized.get("decision_label")).lower()
    if decision_label and decision_label not in ACCEPTED_DECISION_LABELS:
        reasons.append(f"decision_label is invalid: {decision_label}")

    confidence = normalize_text(normalized.get("confidence")).lower()
    if confidence and confidence not in ACCEPTED_CONFIDENCE_VALUES:
        reasons.append(f"confidence is invalid: {confidence}")

    legal_ground_truth_approved, legal_error = parse_false_only_flag(
        "legal_ground_truth_approved",
        normalized.get("legal_ground_truth_approved"),
    )
    if legal_error:
        reasons.append(legal_error)

    rag_index_approved, rag_error = parse_false_only_flag(
        "rag_index_approved",
        normalized.get("rag_index_approved"),
    )
    if rag_error:
        reasons.append(rag_error)

    if reasons:
        return None, InvalidReviewRow(
            row_number=row_number,
            candidate_id=candidate_id,
            reasons=sorted(set(reasons)),
        )

    validated = dict(normalized)
    validated["review_date"] = review_date
    validated["candidate_id"] = candidate_id
    validated["decision_label"] = decision_label
    validated["confidence"] = confidence
    validated["reviewer_id"] = normalize_text(normalized.get("reviewer_id"))
    validated["notes"] = normalize_text(normalized.get("notes"))
    validated["legal_ground_truth_approved"] = bool(legal_ground_truth_approved)
    validated["rag_index_approved"] = bool(rag_index_approved)
    return validated, None


def adjudicate_candidate_reviews(candidate_rows: list[dict[str, Any]]) -> CandidateAdjudication:
    decision_labels = sorted({str(row.get("decision_label") or "") for row in candidate_rows})
    confidence_values = sorted({str(row.get("confidence") or "") for row in candidate_rows})
    reviewer_ids = sorted({str(row.get("reviewer_id") or "") for row in candidate_rows})
    consensus_label = decision_labels[0] if len(decision_labels) == 1 else None

    if consensus_label == "needs_parser_fix":
        status = "parser_fix_required"
    elif consensus_label == "needs_legal_expert_review":
        status = "legal_expert_review_required"
    elif consensus_label == "uncertain":
        status = "uncertain_requires_adjudication"
    elif consensus_label is not None:
        status = "consensus"
    elif any(label == "needs_parser_fix" for label in decision_labels):
        status = "parser_fix_required"
    elif any(label == "needs_legal_expert_review" for label in decision_labels):
        status = "legal_expert_review_required"
    elif any(label == "uncertain" for label in decision_labels):
        status = "uncertain_requires_adjudication"
    else:
        status = "label_conflict_requires_adjudication"

    return CandidateAdjudication(
        candidate_id=str(candidate_rows[0].get("candidate_id") or ""),
        review_count=len(candidate_rows),
        reviewer_ids=reviewer_ids,
        decision_labels=decision_labels,
        confidence_values=confidence_values,
        adjudication_status=status,
        consensus_label=consensus_label,
    )


def adjudicate_review_results(valid_rows: list[dict[str, Any]]) -> list[CandidateAdjudication]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in valid_rows:
        grouped[str(row.get("candidate_id") or "")].append(row)

    adjudications = [
        adjudicate_candidate_reviews(group_rows)
        for _, group_rows in sorted(grouped.items())
    ]
    return adjudications


def report_to_dict(report: ReviewResultsReport) -> dict[str, Any]:
    return {
        "phase": report.phase,
        "review_results_version": report.review_results_version,
        "review_file": report.review_file,
        "total_rows": report.total_rows,
        "valid_rows": report.valid_rows,
        "invalid_rows": report.invalid_rows,
        "decision_counts": report.decision_counts,
        "confidence_counts": report.confidence_counts,
        "adjudication_counts": report.adjudication_counts,
        "distinct_candidate_ids": report.distinct_candidate_ids,
        "distinct_reviewers": report.distinct_reviewers,
        "approved_for_rag_index_true_count": report.approved_for_rag_index_true_count,
        "legal_ground_truth_approved_true_count": report.legal_ground_truth_approved_true_count,
        "invalid_row_details": [asdict(item) for item in report.invalid_row_details],
        "adjudication_results": [asdict(item) for item in report.adjudication_results],
        "safety_verdict": report.safety_verdict,
    }


def validate_review_results_file(path: Path) -> tuple[list[dict[str, Any]], ReviewResultsReport]:
    rows = load_review_results_csv(path)
    valid_rows: list[dict[str, Any]] = []
    invalid_rows: list[InvalidReviewRow] = []

    for row_number, row in enumerate(rows, start=2):
        validated, invalid = validate_review_row(row, row_number)
        if invalid is not None:
            invalid_rows.append(invalid)
            continue
        valid_rows.append(validated or {})

    decision_counts = dict(sorted(Counter(row["decision_label"] for row in valid_rows).items()))
    confidence_counts = dict(sorted(Counter(row["confidence"] for row in valid_rows).items()))
    approved_true = sum(1 for row in valid_rows if bool(row.get("rag_index_approved")) is True)
    ground_truth_true = sum(1 for row in valid_rows if bool(row.get("legal_ground_truth_approved")) is True)
    adjudications = adjudicate_review_results(valid_rows)
    adjudication_counts = dict(
        sorted(Counter(item.adjudication_status for item in adjudications).items())
    )

    if invalid_rows or approved_true > 0 or ground_truth_true > 0:
        verdict = "FAIL"
    elif any(
        item.adjudication_status in {
            "parser_fix_required",
            "legal_expert_review_required",
            "uncertain_requires_adjudication",
            "label_conflict_requires_adjudication",
        }
        for item in adjudications
    ):
        verdict = "PASS WITH RISKS"
    else:
        verdict = "PASS"

    report = ReviewResultsReport(
        phase=PHASE_NAME,
        review_results_version=REVIEW_RESULTS_VERSION,
        review_file=str(path.resolve()),
        total_rows=len(rows),
        valid_rows=len(valid_rows),
        invalid_rows=len(invalid_rows),
        decision_counts=decision_counts,
        confidence_counts=confidence_counts,
        adjudication_counts=adjudication_counts,
        distinct_candidate_ids=len({str(row.get("candidate_id") or "") for row in valid_rows if row.get("candidate_id")}),
        distinct_reviewers=len({str(row.get("reviewer_id") or "") for row in valid_rows if row.get("reviewer_id")}),
        approved_for_rag_index_true_count=approved_true,
        legal_ground_truth_approved_true_count=ground_truth_true,
        invalid_row_details=invalid_rows,
        adjudication_results=adjudications,
        safety_verdict=verdict,
    )
    return valid_rows, report
