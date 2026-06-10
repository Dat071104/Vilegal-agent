from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.validate_review_results import main
from vilegal.ingestion.review_results import (
    ACCEPTED_DECISION_LABELS,
    ACCEPTED_CONFIDENCE_VALUES,
    report_to_dict,
    validate_review_results_file,
)


def make_review_row(**overrides: str) -> dict[str, str]:
    row = {
        "review_sample_id": "phase2h-keep-001-sample",
        "candidate_id": "candidate-001",
        "parent_record_id": "parent-001",
        "source_dataset": "undertheseanlp/UTS_VLC",
        "source_id": "LAW-001",
        "source_url": "https://example.invalid/doc-1",
        "license": "MIT",
        "title": "Luat mau",
        "article_number": "1",
        "article_title": "Dieu 1",
        "filter_decision": "keep_candidate_for_human_review",
        "sampling_bucket": "keep_candidate_for_human_review",
        "reviewer_id": "reviewer-a",
        "review_date": "2026-06-10",
        "decision_label": "accept_for_later_corpus_candidate",
        "confidence": "high",
        "notes": "Structurally article-like.",
        "legal_ground_truth_approved": "false",
        "rag_index_approved": "false",
    }
    row.update(overrides)
    return row


def write_review_csv(path: Path, rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_phase2i_constants_match_rubric_contract() -> None:
    assert set(ACCEPTED_DECISION_LABELS) == {
        "accept_for_later_corpus_candidate",
        "reject_not_article",
        "reject_duplicate",
        "reject_too_short",
        "reject_too_long",
        "reject_missing_metadata",
        "needs_legal_expert_review",
        "needs_parser_fix",
        "uncertain",
    }
    assert tuple(ACCEPTED_CONFIDENCE_VALUES) == ("high", "medium", "low")


def test_validate_review_results_accepts_valid_rows_and_normalizes_false_flags(tmp_path: Path) -> None:
    review_file = write_review_csv(
        tmp_path / "valid.csv",
        [
            make_review_row(),
            make_review_row(
                candidate_id="candidate-002",
                reviewer_id="reviewer-b",
                decision_label="reject_duplicate",
                confidence="medium",
                legal_ground_truth_approved="False",
                rag_index_approved="0",
            ),
        ],
    )

    valid_rows, report = validate_review_results_file(review_file)

    assert len(valid_rows) == 2
    assert report.safety_verdict == "PASS"
    assert report.invalid_rows == 0
    assert report.decision_counts == {
        "accept_for_later_corpus_candidate": 1,
        "reject_duplicate": 1,
    }
    assert all(row["legal_ground_truth_approved"] is False for row in valid_rows)
    assert all(row["rag_index_approved"] is False for row in valid_rows)


def test_validate_review_results_rejects_invalid_rows_and_reports_reasons(tmp_path: Path) -> None:
    review_file = write_review_csv(
        tmp_path / "invalid.csv",
        [
            make_review_row(
                candidate_id="",
                decision_label="bad_label",
                confidence="certain",
                legal_ground_truth_approved="true",
                rag_index_approved="yes",
                notes="",
            ),
        ],
    )

    _, report = validate_review_results_file(review_file)

    assert report.safety_verdict == "FAIL"
    assert report.valid_rows == 0
    assert report.invalid_rows == 1
    reasons = report.invalid_row_details[0].reasons
    assert "candidate_id is required." in reasons
    assert "decision_label is invalid: bad_label" in reasons
    assert "confidence is invalid: certain" in reasons
    assert "notes is required." in reasons
    assert "legal_ground_truth_approved must remain false in Phase 2I." in reasons
    assert "rag_index_approved must remain false in Phase 2I." in reasons


def test_validate_review_results_reports_counts_and_conflict_adjudication(tmp_path: Path) -> None:
    review_file = write_review_csv(
        tmp_path / "conflict.csv",
        [
            make_review_row(candidate_id="candidate-001", reviewer_id="reviewer-a"),
            make_review_row(
                candidate_id="candidate-001",
                reviewer_id="reviewer-b",
                decision_label="reject_too_long",
                confidence="medium",
            ),
            make_review_row(
                candidate_id="candidate-002",
                reviewer_id="reviewer-c",
                decision_label="needs_parser_fix",
                confidence="low",
            ),
        ],
    )

    _, report = validate_review_results_file(review_file)

    assert report.safety_verdict == "PASS WITH RISKS"
    assert report.decision_counts == {
        "accept_for_later_corpus_candidate": 1,
        "needs_parser_fix": 1,
        "reject_too_long": 1,
    }
    assert report.adjudication_counts == {
        "label_conflict_requires_adjudication": 1,
        "parser_fix_required": 1,
    }
    by_candidate = {item.candidate_id: item for item in report.adjudication_results}
    assert by_candidate["candidate-001"].adjudication_status == "label_conflict_requires_adjudication"
    assert by_candidate["candidate-002"].adjudication_status == "parser_fix_required"


def test_cli_writes_report_for_valid_fixture(tmp_path: Path) -> None:
    review_file = write_review_csv(tmp_path / "valid.csv", [make_review_row()])
    report_path = tmp_path / "report.json"

    exit_code = main(
        [
            "--review-file",
            str(review_file),
            "--report-out",
            str(report_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["safety_verdict"] == "PASS"
    assert payload["valid_rows"] == 1


def test_report_to_dict_serializes_dataclasses(tmp_path: Path) -> None:
    review_file = write_review_csv(
        tmp_path / "needs_review.csv",
        [make_review_row(decision_label="needs_legal_expert_review", confidence="low")],
    )

    _, report = validate_review_results_file(review_file)
    payload = report_to_dict(report)

    assert payload["phase"].startswith("Phase 2I")
    assert payload["adjudication_results"][0]["adjudication_status"] == "legal_expert_review_required"
