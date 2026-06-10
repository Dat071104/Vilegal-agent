#!/usr/bin/env python3
"""
Phase 2J helper for bulk-filling a completed human review CSV from the
Phase 2H reviewer decision template.

This helper never approves legal ground truth and never approves RAG indexing.
It only writes a completed CSV after explicit human confirmation flags are
passed on the command line.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.ingestion.review_results import (  # noqa: E402
    ACCEPTED_CONFIDENCE_VALUES,
    ACCEPTED_DECISION_LABELS,
    REQUIRED_REVIEW_RESULT_FIELDS,
)

DEFAULT_DECISION_LABEL = "accept_for_later_corpus_candidate"
DEFAULT_CONFIDENCE = "medium"
FALSE_TEXT = "false"

REQUIRED_CONFIRMATION_FLAGS = (
    "i_confirm_human_reviewed",
    "i_understand_not_legal_ground_truth",
    "i_understand_not_rag_approved",
)


@dataclass(frozen=True)
class FillSummary:
    rows_written: int
    decision_label: str
    confidence: str
    reviewer_id: str
    review_date: str
    output_path: str
    legal_ground_truth_approved_true_count: int
    rag_index_approved_true_count: int


def resolve_artifacts_root() -> Path:
    return (ROOT / "artifacts").resolve()


def ensure_path_within_artifacts(path: Path) -> Path:
    resolved = path.resolve()
    artifacts_root = resolve_artifacts_root()
    if resolved != artifacts_root and artifacts_root not in resolved.parents:
        raise ValueError(f"Path must stay under artifacts/: {resolved}")
    return resolved


def validate_review_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError("review_date must be ISO format YYYY-MM-DD.") from exc


def ensure_confirmations(args: argparse.Namespace) -> None:
    missing = [
        f"--{name.replace('_', '-')}"
        for name in REQUIRED_CONFIRMATION_FLAGS
        if not getattr(args, name, False)
    ]
    if missing:
        raise ValueError(
            "Missing required confirmation flags: " + ", ".join(missing)
        )


def normalize_fieldnames(fieldnames: list[str] | None) -> list[str]:
    existing = list(fieldnames or [])
    for field_name in REQUIRED_REVIEW_RESULT_FIELDS:
        if field_name not in existing:
            existing.append(field_name)
    return existing


def build_completed_row(
    row: dict[str, str],
    reviewer_id: str,
    review_date: str,
    decision_label: str,
    confidence: str,
    notes: str,
    fieldnames: list[str],
) -> dict[str, str]:
    completed = {name: row.get(name, "") for name in fieldnames}
    completed["reviewer_id"] = reviewer_id
    completed["review_date"] = review_date
    completed["candidate_id"] = str(row.get("candidate_id", "")).strip()
    completed["decision_label"] = decision_label
    completed["confidence"] = confidence
    completed["notes"] = notes
    completed["legal_ground_truth_approved"] = FALSE_TEXT
    completed["rag_index_approved"] = FALSE_TEXT
    return completed


def write_completed_reviews(
    template_path: Path,
    output_path: Path,
    reviewer_id: str,
    review_date: str,
    decision_label: str,
    confidence: str,
    notes: str,
) -> FillSummary:
    with template_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = normalize_fieldnames(reader.fieldnames)
        rows = [
            build_completed_row(
                row=row,
                reviewer_id=reviewer_id,
                review_date=review_date,
                decision_label=decision_label,
                confidence=confidence,
                notes=notes,
                fieldnames=fieldnames,
            )
            for row in reader
        ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return FillSummary(
        rows_written=len(rows),
        decision_label=decision_label,
        confidence=confidence,
        reviewer_id=reviewer_id,
        review_date=review_date,
        output_path=str(output_path),
        legal_ground_truth_approved_true_count=0,
        rag_index_approved_true_count=0,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bulk-fill a completed Phase 2H reviewer decisions CSV after explicit human confirmation."
    )
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reviewer-id", required=True)
    parser.add_argument(
        "--decision-label",
        default=DEFAULT_DECISION_LABEL,
        choices=ACCEPTED_DECISION_LABELS,
    )
    parser.add_argument(
        "--confidence",
        default=DEFAULT_CONFIDENCE,
        choices=ACCEPTED_CONFIDENCE_VALUES,
    )
    parser.add_argument("--notes", required=True)
    parser.add_argument(
        "--review-date",
        default=date.today().isoformat(),
        help="ISO date to write into review_date. Defaults to today's local date.",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--i-confirm-human-reviewed", action="store_true")
    parser.add_argument("--i-understand-not-legal-ground-truth", action="store_true")
    parser.add_argument("--i-understand-not-rag-approved", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        ensure_confirmations(args)
        review_date = validate_review_date(args.review_date)
        template_path = args.template.resolve()
        output_path = ensure_path_within_artifacts(args.output)

        if template_path == output_path:
            raise ValueError("Output path must be different from the template path.")
        if not template_path.exists():
            raise FileNotFoundError(f"Template file does not exist: {template_path}")
        if not template_path.is_file():
            raise ValueError(f"Template path is not a file: {template_path}")
        if output_path.exists() and not args.overwrite:
            raise FileExistsError(
                f"Output file already exists. Pass --overwrite to replace it: {output_path}"
            )

        summary = write_completed_reviews(
            template_path=template_path,
            output_path=output_path,
            reviewer_id=str(args.reviewer_id).strip(),
            review_date=review_date,
            decision_label=str(args.decision_label).strip(),
            confidence=str(args.confidence).strip(),
            notes=str(args.notes).strip(),
        )
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"rows_written={summary.rows_written}")
    print(f"decision_label={summary.decision_label}")
    print(f"confidence={summary.confidence}")
    print(f"output_path={summary.output_path}")
    print(
        "legal_ground_truth_approved_true_count="
        f"{summary.legal_ground_truth_approved_true_count}"
    )
    print(f"rag_index_approved_true_count={summary.rag_index_approved_true_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
