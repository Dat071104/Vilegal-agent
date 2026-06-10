from __future__ import annotations

import json
from pathlib import Path

from scripts.filter_uts_article_candidates import main
from vilegal.ingestion.article_filter import (
    DECISION_KEEP,
    DECISION_NEEDS_REVIEW_MARKER,
    DECISION_NEEDS_REVIEW_PREAMBLE,
    DECISION_NEEDS_REVIEW_SUSPICIOUS_LENGTH,
    DECISION_REJECT_DUPLICATE_HASH,
    DECISION_REJECT_EMPTY,
    DECISION_REJECT_MISSING_PARENT_PROVENANCE,
    DECISION_REJECT_NEAR_EMPTY,
    classify_candidates,
    compute_metrics,
)


def make_candidate(**overrides) -> dict:
    base = {
        "parent_record_id": "parent-001",
        "source_dataset": "undertheseanlp/UTS_VLC",
        "source_id": "91/2015/QH13",
        "source_url": "https://example.invalid/doc",
        "license": "MIT",
        "retrieved_at": "2026-06-09T00:00:00Z",
        "title": "Bo luat",
        "article_number": 1,
        "article_title": "Pham vi dieu chinh",
        "chunk_index": 0,
        "text": "Dieu 1. Pham vi dieu chinh " + ("Noi dung " * 30),
        "text_hash": "hash-001",
        "parser_version": "phase_2f_v1",
        "parse_flags": [],
        "uncertain_parse": False,
        "is_legal_ground_truth": False,
        "approved_for_rag_index": False,
    }
    base.update(overrides)
    return base


def make_warning(parent_record_id: str, code: str) -> dict:
    return {
        "parent_record_id": parent_record_id,
        "source_id": "91/2015/QH13",
        "code": code,
        "message": code,
    }


def test_missing_parent_provenance_rejects_candidate():
    candidate = make_candidate(source_id="")
    all_records, rejected, needs_review, dupes = classify_candidates([candidate], [])
    assert all_records[0]["filter_decision"] == DECISION_REJECT_MISSING_PARENT_PROVENANCE
    assert len(rejected) == 1


def test_missing_parent_record_id_rejects_candidate():
    candidate = make_candidate(parent_record_id="")
    all_records, rejected, needs_review, dupes = classify_candidates([candidate], [])
    assert all_records[0]["filter_decision"] == DECISION_REJECT_MISSING_PARENT_PROVENANCE


def test_missing_article_text_rejects_candidate():
    candidate = make_candidate(text="")
    all_records, rejected, needs_review, dupes = classify_candidates([candidate], [])
    assert all_records[0]["filter_decision"] == DECISION_REJECT_EMPTY


def test_empty_candidate_rejected():
    candidate = make_candidate(text="   ")
    all_records, rejected, needs_review, dupes = classify_candidates([candidate], [])
    assert all_records[0]["filter_decision"] == DECISION_REJECT_EMPTY


def test_near_empty_candidate_rejected():
    candidate = make_candidate(text="Dieu 1. Ngan")
    all_records, rejected, needs_review, dupes = classify_candidates([candidate], [])
    assert all_records[0]["filter_decision"] == DECISION_REJECT_NEAR_EMPTY


def test_duplicate_hash_groups_counted_and_loser_rejected():
    first = make_candidate(text_hash="dup-hash", text="Dieu 1. " + ("Noi dung " * 30))
    second = make_candidate(parent_record_id="parent-002", text_hash="dup-hash", text="Dieu 2. " + ("Noi dung " * 30))
    all_records, rejected, needs_review, dupes = classify_candidates([first, second], [])
    assert dupes == {"dup-hash": 2}
    assert sum(1 for item in all_records if item["filter_decision"] == DECISION_REJECT_DUPLICATE_HASH) == 1
    loser = next(item for item in all_records if item["filter_decision"] == DECISION_REJECT_DUPLICATE_HASH)
    assert loser["duplicate_of"] is not None


def test_duplicate_metrics_follow_hash_group_formula_for_exact_copies():
    candidate = make_candidate(text_hash="dup-hash")
    all_records, rejected, needs_review, dupes = classify_candidates([candidate, dict(candidate)], [])
    metrics = compute_metrics([candidate, dict(candidate)], all_records, rejected, needs_review, dupes, 0)
    assert dupes == {"dup-hash": 2}
    assert metrics.duplicate_hash_groups == 1
    assert metrics.duplicate_candidates_rejected == 1


def test_suspicious_short_candidate_marked_needs_review():
    candidate = make_candidate(text=("word " * 11) + ("x" * 44))
    all_records, rejected, needs_review, dupes = classify_candidates([candidate], [])
    assert all_records[0]["filter_decision"] == DECISION_NEEDS_REVIEW_SUSPICIOUS_LENGTH


def test_candidate_level_header_noise_marked_needs_review():
    candidate = make_candidate(parse_flags=["markdown_heading_marker"])
    all_records, rejected, needs_review, dupes = classify_candidates([candidate], [])
    assert all_records[0]["filter_decision"] == DECISION_NEEDS_REVIEW_PREAMBLE


def test_parent_document_warning_does_not_force_needs_review():
    candidate = make_candidate()
    warnings = [make_warning("parent-001", "preamble_before_first_article")]
    all_records, rejected, needs_review, dupes = classify_candidates([candidate], warnings)
    metrics = compute_metrics([candidate], all_records, rejected, needs_review, dupes, len(warnings))
    assert all_records[0]["filter_decision"] == DECISION_KEEP
    assert all_records[0]["parent_document_warning_codes"] == ["preamble_before_first_article"]
    assert any(flag.startswith("parent_document_warning:") for flag in all_records[0]["risk_flags"])
    assert metrics.parent_document_warning_count == 1
    assert metrics.preamble_warning_count == 0


def test_marker_uncertainty_marked_needs_review():
    candidate = make_candidate(parse_flags=["article_title_missing"], uncertain_parse=True)
    all_records, rejected, needs_review, dupes = classify_candidates([candidate], [])
    assert all_records[0]["filter_decision"] == DECISION_NEEDS_REVIEW_MARKER


def test_clean_candidate_kept_for_human_review():
    candidate = make_candidate()
    all_records, rejected, needs_review, dupes = classify_candidates([candidate], [])
    assert all_records[0]["filter_decision"] == DECISION_KEEP


def test_safety_flags_always_false_for_all_outputs():
    candidates = [
        make_candidate(),
        make_candidate(parent_record_id="parent-002", text="Dieu 2. ngan"),
    ]
    all_records, rejected, needs_review, dupes = classify_candidates(candidates, [])
    assert all(item["approved_for_rag_index"] is False for item in all_records)
    assert all(item["is_legal_ground_truth"] is False for item in all_records)


def test_report_reconciliation_holds():
    candidates = [
        make_candidate(),
        make_candidate(parent_record_id="parent-002", text="Dieu 2. ngan"),
        make_candidate(parent_record_id="parent-003", parse_flags=["article_title_missing"], uncertain_parse=True),
    ]
    all_records, rejected, needs_review, dupes = classify_candidates(candidates, [])
    metrics = compute_metrics(candidates, all_records, rejected, needs_review, dupes, 0)
    assert metrics.total_input_candidates == (
        metrics.total_rejected
        + metrics.total_needs_review
        + metrics.total_keep_candidate_for_human_review
    )


def test_determinism_same_input_same_decisions():
    candidates = [
        make_candidate(),
        make_candidate(parent_record_id="parent-002", text_hash="dup", text="Dieu 2. " + ("Noi dung " * 30)),
        make_candidate(parent_record_id="parent-003", text_hash="dup", text="Dieu 3. " + ("Noi dung " * 30)),
    ]
    warnings = [make_warning("parent-001", "preamble_before_first_article")]
    result_a = classify_candidates(candidates, warnings)
    result_b = classify_candidates(candidates, warnings)
    assert [item["filter_decision"] for item in result_a[0]] == [item["filter_decision"] for item in result_b[0]]
    assert result_a[3] == result_b[3]


def test_cli_fails_if_input_dir_missing(tmp_path: Path):
    output_dir = tmp_path / "repo" / "artifacts" / "phase_2g_uts_filtering"
    report_out = tmp_path / "repo" / "artifacts" / "phase_2g_uts_filtering_report.json"
    import scripts.filter_uts_article_candidates as cli

    original_root = cli.ROOT
    try:
        cli.ROOT = tmp_path / "repo"
        exit_code = main(
            [
                "--input-dir",
                str(tmp_path / "missing"),
                "--output-dir",
                str(output_dir),
                "--report-out",
                str(report_out),
            ]
        )
        assert exit_code != 0
        assert not output_dir.exists()
    finally:
        cli.ROOT = original_root


def test_cli_refuses_output_outside_artifacts(tmp_path: Path):
    repo = tmp_path / "repo"
    input_dir = repo / "artifacts" / "phase_2f_uts_article_candidates"
    input_dir.mkdir(parents=True)
    for name, content in {
        "article_candidates.jsonl": json.dumps(make_candidate()) + "\n",
        "parse_report.json": json.dumps({"input_dir": str(repo / "artifacts" / "phase_2d_controlled_ingestion" / "uts_vlc")}),
        "parse_warnings.jsonl": "",
    }.items():
        (input_dir / name).write_text(content, encoding="utf-8")
    import scripts.filter_uts_article_candidates as cli

    original_root = cli.ROOT
    try:
        cli.ROOT = repo
        exit_code = main(
            [
                "--input-dir",
                str(input_dir),
                "--output-dir",
                str(repo / "outside"),
            ]
        )
        assert exit_code != 0
    finally:
        cli.ROOT = original_root


def test_cli_no_partial_candidate_outputs_when_manifest_missing(tmp_path: Path):
    repo = tmp_path / "repo"
    input_dir = repo / "artifacts" / "phase_2f_uts_article_candidates"
    output_dir = repo / "artifacts" / "phase_2g_uts_filtering"
    input_dir.mkdir(parents=True)
    phase2d_dir = repo / "artifacts" / "phase_2d_controlled_ingestion" / "uts_vlc"
    phase2d_dir.mkdir(parents=True)
    (input_dir / "article_candidates.jsonl").write_text(json.dumps(make_candidate()) + "\n", encoding="utf-8")
    (input_dir / "parse_report.json").write_text(json.dumps({"input_dir": str(phase2d_dir)}), encoding="utf-8")
    (input_dir / "parse_warnings.jsonl").write_text("", encoding="utf-8")

    import scripts.filter_uts_article_candidates as cli

    original_root = cli.ROOT
    try:
        cli.ROOT = repo
        exit_code = main(
            [
                "--input-dir",
                str(input_dir),
                "--output-dir",
                str(output_dir),
            ]
        )
        assert exit_code != 0
        assert not (output_dir / "filtered_candidates.jsonl").exists()
        report = json.loads((output_dir / "filter_report.json").read_text(encoding="utf-8"))
        assert report["blocked"] is True
    finally:
        cli.ROOT = original_root
