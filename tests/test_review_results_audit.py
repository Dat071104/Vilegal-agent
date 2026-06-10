from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.audit_review_results import main
from vilegal.ingestion.review_audit import BLOCKED_STATUS, audit_review_results


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


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def test_valid_completed_review_file_audit_writes_outputs(tmp_path: Path) -> None:
    review_file = write_review_csv(
        tmp_path / "completed.csv",
        [
            make_review_row(candidate_id="candidate-001"),
            make_review_row(
                candidate_id="candidate-002",
                decision_label="reject_duplicate",
                reviewer_id="reviewer-b",
                confidence="medium",
            ),
        ],
    )
    output_dir = tmp_path / "artifacts" / "phase_2j_review_results_audit"

    report, outputs = audit_review_results(review_file, output_dir)

    assert report.status == "PASS"
    assert report.metrics.accepted_for_later_corpus_candidate_count == 1
    assert report.metrics.rejected_count == 1
    assert report.metrics.unresolved_count == 0
    assert (output_dir / "review_results_audit.json").exists()
    assert len(outputs["accepted"]) == 1
    assert len(outputs["rejected"]) == 1
    assert load_jsonl(output_dir / "accepted_candidate_ids_for_later_review.jsonl")[0]["phase3_ready"] is False


def test_missing_review_file_returns_blocked_status_and_no_candidate_outputs(tmp_path: Path) -> None:
    review_file = tmp_path / "missing.csv"
    output_dir = tmp_path / "artifacts" / "phase_2j_review_results_audit"

    report, outputs = audit_review_results(review_file, output_dir)

    assert report.status == BLOCKED_STATUS
    assert report.blocked is True
    assert outputs == {}
    assert (output_dir / "review_results_audit.json").exists()
    assert not (output_dir / "accepted_candidate_ids_for_later_review.jsonl").exists()
    assert not (output_dir / "rejected_candidate_ids.jsonl").exists()
    assert not (output_dir / "unresolved_candidate_ids.jsonl").exists()


def test_invalid_labels_are_rejected(tmp_path: Path) -> None:
    review_file = write_review_csv(
        tmp_path / "invalid.csv",
        [make_review_row(decision_label="bad_label")],
    )
    output_dir = tmp_path / "artifacts" / "phase_2j_review_results_audit"

    report, _ = audit_review_results(review_file, output_dir)

    assert report.status == "FAIL"
    assert report.metrics.invalid_rows == 1
    assert report.validation_report["invalid_row_details"][0]["reasons"][0].startswith("decision_label is invalid")


def test_duplicate_candidate_reviews_are_detected(tmp_path: Path) -> None:
    review_file = write_review_csv(
        tmp_path / "duplicates.csv",
        [
            make_review_row(candidate_id="candidate-001", reviewer_id="reviewer-a"),
            make_review_row(candidate_id="candidate-001", reviewer_id="reviewer-b", confidence="medium"),
        ],
    )
    output_dir = tmp_path / "artifacts" / "phase_2j_review_results_audit"

    report, _ = audit_review_results(review_file, output_dir)

    assert report.metrics.duplicate_candidate_review_count == 1
    assert report.status == "PASS WITH RISKS"


def test_conflicting_candidate_decisions_are_detected(tmp_path: Path) -> None:
    review_file = write_review_csv(
        tmp_path / "conflicts.csv",
        [
            make_review_row(candidate_id="candidate-001", reviewer_id="reviewer-a"),
            make_review_row(
                candidate_id="candidate-001",
                reviewer_id="reviewer-b",
                decision_label="reject_too_long",
                confidence="medium",
            ),
        ],
    )
    output_dir = tmp_path / "artifacts" / "phase_2j_review_results_audit"

    report, outputs = audit_review_results(review_file, output_dir)

    assert report.metrics.conflict_count == 1
    assert report.metrics.unresolved_count == 1
    assert outputs["unresolved"][0]["adjudication_status"] == "label_conflict_requires_adjudication"


def test_low_confidence_rate_is_calculated(tmp_path: Path) -> None:
    review_file = write_review_csv(
        tmp_path / "low-confidence.csv",
        [
            make_review_row(candidate_id="candidate-001", confidence="low"),
            make_review_row(candidate_id="candidate-002", confidence="high", reviewer_id="reviewer-b"),
        ],
    )
    output_dir = tmp_path / "artifacts" / "phase_2j_review_results_audit"

    report, _ = audit_review_results(review_file, output_dir)

    assert report.metrics.low_confidence_rate == 0.5


def test_legal_ground_truth_true_fails_closed(tmp_path: Path) -> None:
    review_file = write_review_csv(
        tmp_path / "ground-truth.csv",
        [make_review_row(legal_ground_truth_approved="true")],
    )
    output_dir = tmp_path / "artifacts" / "phase_2j_review_results_audit"

    report, _ = audit_review_results(review_file, output_dir)

    assert report.status == "FAIL"
    assert report.metrics.legal_ground_truth_approved_true_count == 1


def test_rag_index_true_fails_closed(tmp_path: Path) -> None:
    review_file = write_review_csv(
        tmp_path / "rag.csv",
        [make_review_row(rag_index_approved="true")],
    )
    output_dir = tmp_path / "artifacts" / "phase_2j_review_results_audit"

    report, _ = audit_review_results(review_file, output_dir)

    assert report.status == "FAIL"
    assert report.metrics.rag_index_approved_true_count == 1


def test_cli_output_path_must_be_under_artifacts(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    review_file = write_review_csv(repo / "completed.csv", [make_review_row()])

    import scripts.audit_review_results as cli

    original_root = cli.ROOT
    try:
        cli.ROOT = repo
        exit_code = main(
            [
                "--review-file",
                str(review_file),
                "--output-dir",
                str(repo / "outside"),
            ]
        )
    finally:
        cli.ROOT = original_root

    assert exit_code == 2


def test_no_synthetic_fixture_is_treated_as_real_approval(tmp_path: Path) -> None:
    review_file = write_review_csv(
        tmp_path / "completed.csv",
        [make_review_row(candidate_id="candidate-001")],
    )
    output_dir = tmp_path / "artifacts" / "phase_2j_review_results_audit"

    report, _ = audit_review_results(review_file, output_dir)
    accepted_rows = load_jsonl(output_dir / "accepted_candidate_ids_for_later_review.jsonl")

    assert report.status == "PASS"
    assert accepted_rows[0]["legal_ground_truth_approved"] is False
    assert accepted_rows[0]["rag_index_approved"] is False
    assert accepted_rows[0]["phase3_ready"] is False
