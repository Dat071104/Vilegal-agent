"""
review_audit.py - Phase 2J review-result audit utilities.

Audits completed human-review CSV files using the Phase 2I validation layer.
This module never fabricates human labels, never promotes legal ground truth,
and never approves any candidate for RAG indexing.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from vilegal.ingestion.review_results import (
    CandidateAdjudication,
    load_review_results_csv,
    report_to_dict as validation_report_to_dict,
    validate_review_results_file,
)

PHASE_NAME = "Phase 2J - Review Results Import + Human Label Quality Audit"
REVIEW_AUDIT_VERSION = "phase_2j_v1"
BLOCKED_STATUS = "BLOCKED FOR REAL HUMAN REVIEW"

FALSE_VALUES = {"false", "0", "no", "n"}
TRUE_VALUES = {"true", "1", "yes", "y"}


@dataclass
class ReviewAuditMetrics:
    total_rows: int
    valid_rows: int
    invalid_rows: int
    decision_counts: dict[str, int]
    confidence_counts: dict[str, int]
    low_confidence_rate: float
    missing_candidate_id_count: int
    duplicate_candidate_review_count: int
    conflict_count: int
    accepted_for_later_corpus_candidate_count: int
    rejected_count: int
    unresolved_count: int
    legal_ground_truth_approved_true_count: int
    rag_index_approved_true_count: int


@dataclass
class ReviewAuditReport:
    phase: str
    review_audit_version: str
    review_file: str
    output_dir: str
    status: str
    blocked: bool
    reason: str
    file_exists: bool
    metrics: ReviewAuditMetrics
    validation_report: dict[str, Any] = field(default_factory=dict)
    candidate_outputs: dict[str, str] = field(default_factory=dict)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def is_true_value(raw_value: Any) -> bool:
    return normalize_text(raw_value).lower() in TRUE_VALUES


def empty_metrics() -> ReviewAuditMetrics:
    return ReviewAuditMetrics(
        total_rows=0,
        valid_rows=0,
        invalid_rows=0,
        decision_counts={},
        confidence_counts={},
        low_confidence_rate=0.0,
        missing_candidate_id_count=0,
        duplicate_candidate_review_count=0,
        conflict_count=0,
        accepted_for_later_corpus_candidate_count=0,
        rejected_count=0,
        unresolved_count=0,
        legal_ground_truth_approved_true_count=0,
        rag_index_approved_true_count=0,
    )


def blocked_report(review_file: Path, output_dir: Path, reason: str) -> ReviewAuditReport:
    return ReviewAuditReport(
        phase=PHASE_NAME,
        review_audit_version=REVIEW_AUDIT_VERSION,
        review_file=str(review_file.resolve()),
        output_dir=str(output_dir.resolve()),
        status=BLOCKED_STATUS,
        blocked=True,
        reason=reason,
        file_exists=False,
        metrics=empty_metrics(),
        validation_report={},
        candidate_outputs={},
    )


def candidate_output_paths(output_dir: Path) -> dict[str, str]:
    return {
        "review_results_audit_json": str((output_dir / "review_results_audit.json").resolve()),
        "accepted_candidate_ids_for_later_review_jsonl": str(
            (output_dir / "accepted_candidate_ids_for_later_review.jsonl").resolve()
        ),
        "rejected_candidate_ids_jsonl": str((output_dir / "rejected_candidate_ids.jsonl").resolve()),
        "unresolved_candidate_ids_jsonl": str((output_dir / "unresolved_candidate_ids.jsonl").resolve()),
    }


def candidate_review_counts(valid_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(row.get("candidate_id") or "") for row in valid_rows if row.get("candidate_id"))
    return dict(sorted(counts.items()))


def classify_candidate(adjudication: CandidateAdjudication) -> str:
    if adjudication.adjudication_status == "consensus":
        if adjudication.consensus_label == "accept_for_later_corpus_candidate":
            return "accepted_for_later_review"
        if str(adjudication.consensus_label or "").startswith("reject_"):
            return "rejected"
    return "unresolved"


def candidate_output_row(
    adjudication: CandidateAdjudication,
    bucket: str,
) -> dict[str, Any]:
    return {
        "candidate_id": adjudication.candidate_id,
        "bucket": bucket,
        "consensus_label": adjudication.consensus_label,
        "adjudication_status": adjudication.adjudication_status,
        "review_count": adjudication.review_count,
        "reviewer_ids": adjudication.reviewer_ids,
        "legal_ground_truth_approved": False,
        "rag_index_approved": False,
        "phase3_ready": False,
    }


def build_candidate_outputs(
    adjudications: list[CandidateAdjudication],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    for adjudication in adjudications:
        bucket = classify_candidate(adjudication)
        row = candidate_output_row(adjudication, bucket)
        if bucket == "accepted_for_later_review":
            accepted.append(row)
        elif bucket == "rejected":
            rejected.append(row)
        else:
            unresolved.append(row)

    return accepted, rejected, unresolved


def compute_metrics(
    raw_rows: list[dict[str, Any]],
    valid_rows: list[dict[str, Any]],
    adjudications: list[CandidateAdjudication],
) -> ReviewAuditMetrics:
    total_rows = len(raw_rows)
    valid_count = len(valid_rows)
    invalid_count = total_rows - valid_count
    decision_counts = dict(sorted(Counter(str(row.get("decision_label") or "") for row in valid_rows).items()))
    confidence_counts = dict(sorted(Counter(str(row.get("confidence") or "") for row in valid_rows).items()))
    low_confidence_rate = round(
        sum(1 for row in valid_rows if str(row.get("confidence") or "") == "low") / valid_count,
        6,
    ) if valid_count else 0.0
    missing_candidate_id_count = sum(1 for row in raw_rows if not normalize_text(row.get("candidate_id")))
    raw_ground_truth_true_count = sum(
        1 for row in raw_rows if is_true_value(row.get("legal_ground_truth_approved"))
    )
    raw_rag_true_count = sum(
        1 for row in raw_rows if is_true_value(row.get("rag_index_approved"))
    )
    review_counts = candidate_review_counts(valid_rows)
    duplicate_candidate_review_count = sum(1 for count in review_counts.values() if count > 1)
    conflict_count = sum(
        1
        for item in adjudications
        if item.adjudication_status == "label_conflict_requires_adjudication"
    )
    accepted, rejected, unresolved = build_candidate_outputs(adjudications)

    return ReviewAuditMetrics(
        total_rows=total_rows,
        valid_rows=valid_count,
        invalid_rows=invalid_count,
        decision_counts=decision_counts,
        confidence_counts=confidence_counts,
        low_confidence_rate=low_confidence_rate,
        missing_candidate_id_count=missing_candidate_id_count,
        duplicate_candidate_review_count=duplicate_candidate_review_count,
        conflict_count=conflict_count,
        accepted_for_later_corpus_candidate_count=len(accepted),
        rejected_count=len(rejected),
        unresolved_count=len(unresolved),
        legal_ground_truth_approved_true_count=raw_ground_truth_true_count,
        rag_index_approved_true_count=raw_rag_true_count,
    )


def report_to_dict(report: ReviewAuditReport) -> dict[str, Any]:
    return {
        "phase": report.phase,
        "review_audit_version": report.review_audit_version,
        "review_file": report.review_file,
        "output_dir": report.output_dir,
        "status": report.status,
        "blocked": report.blocked,
        "reason": report.reason,
        "file_exists": report.file_exists,
        "metrics": asdict(report.metrics),
        "validation_report": report.validation_report,
        "candidate_outputs": report.candidate_outputs,
    }


def audit_review_results(review_file: Path, output_dir: Path) -> tuple[ReviewAuditReport, dict[str, list[dict[str, Any]]]]:
    if not review_file.exists():
        report = blocked_report(
            review_file,
            output_dir,
            "Completed human review file is missing. Phase 2J cannot audit real review outcomes yet.",
        )
        write_json(output_dir / "review_results_audit.json", report_to_dict(report))
        return report, {}

    raw_rows = load_review_results_csv(review_file)
    valid_rows, validation_report = validate_review_results_file(review_file)
    adjudications = validation_report.adjudication_results
    metrics = compute_metrics(raw_rows, valid_rows, adjudications)
    accepted, rejected, unresolved = build_candidate_outputs(adjudications)

    if (
        metrics.legal_ground_truth_approved_true_count > 0
        or metrics.rag_index_approved_true_count > 0
        or metrics.invalid_rows > 0
    ):
        status = "FAIL"
        reason = (
            "Review results failed closed because invalid rows or forbidden approval flags were detected."
        )
    elif (
        metrics.low_confidence_rate > 0
        or metrics.duplicate_candidate_review_count > 0
        or metrics.conflict_count > 0
        or metrics.unresolved_count > 0
    ):
        status = "PASS WITH RISKS"
        reason = "Review results audited successfully, but downstream use remains review-only."
    else:
        status = "PASS"
        reason = "Review results audited successfully with no unresolved candidate outcomes."

    paths = candidate_output_paths(output_dir)
    report = ReviewAuditReport(
        phase=PHASE_NAME,
        review_audit_version=REVIEW_AUDIT_VERSION,
        review_file=str(review_file.resolve()),
        output_dir=str(output_dir.resolve()),
        status=status,
        blocked=False,
        reason=reason,
        file_exists=True,
        metrics=metrics,
        validation_report=validation_report_to_dict(validation_report),
        candidate_outputs=paths if status != "FAIL" else {},
    )

    write_json(output_dir / "review_results_audit.json", report_to_dict(report))

    outputs = {
        "accepted": accepted,
        "rejected": rejected,
        "unresolved": unresolved,
    }
    if status != "FAIL":
        write_jsonl(output_dir / "accepted_candidate_ids_for_later_review.jsonl", accepted)
        write_jsonl(output_dir / "rejected_candidate_ids.jsonl", rejected)
        write_jsonl(output_dir / "unresolved_candidate_ids.jsonl", unresolved)

    return report, outputs
