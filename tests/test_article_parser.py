from __future__ import annotations

import json
from pathlib import Path

from scripts.parse_uts_vlc_articles import ensure_safe_output_paths, main
from vilegal.ingestion.article_parser import (
    PARSER_VERSION,
    detect_article_markers,
    derive_candidates_from_document,
    duplicate_hash_count,
)


def make_parent_record(text: str) -> dict:
    return {
        "record_id": "parent-001",
        "source_dataset": "undertheseanlp/UTS_VLC",
        "source_id": "91/2015/QH13",
        "source_url": "https://example.invalid/uts/91-2015",
        "license": "MIT",
        "retrieved_at": "2026-06-09T00:00:00Z",
        "title": "Bo luat dan su",
        "document_type": "other",
        "document_number": "",
        "text": text,
    }


def test_detect_article_markers_supports_multiple_formats():
    text = "Dieu 1. Pham vi dieu chinh\nNoi dung\nDieu 2: Giai thich tu ngu"
    markers = detect_article_markers(text)
    assert [marker.article_number for marker in markers] == [1, 2]


def test_detect_article_markers_supports_markdown_headings():
    text = "# Dieu 1. Pham vi\nNoi dung"
    markers = detect_article_markers(text)
    assert len(markers) == 1
    assert markers[0].is_markdown_heading is True


def test_no_split_when_no_article_markers():
    record = make_parent_record("Mo dau khong co marker hop le.")
    candidates, warnings, rejected = derive_candidates_from_document(record)
    assert candidates == []
    assert rejected is not None
    assert rejected.reason == "no_article_markers_detected"


def test_parent_metadata_preserved_on_candidate():
    record = make_parent_record("Dieu 1. Pham vi dieu chinh\nNoi dung cua dieu 1.")
    candidates, warnings, rejected = derive_candidates_from_document(record)
    assert rejected is None
    candidate = candidates[0]
    assert candidate["source_dataset"] == record["source_dataset"]
    assert candidate["source_id"] == record["source_id"]
    assert candidate["source_url"] == record["source_url"]
    assert candidate["license"] == record["license"]
    assert candidate["retrieved_at"] == record["retrieved_at"]
    assert candidate["parent_record_id"] == record["record_id"]


def test_missing_provenance_fails_closed():
    record = make_parent_record("Dieu 1. Pham vi dieu chinh\nNoi dung.")
    record["license"] = ""
    candidates, warnings, rejected = derive_candidates_from_document(record)
    assert candidates == []
    assert rejected is not None
    assert "license" in rejected.missing_fields


def test_duplicate_text_hash_detection():
    candidates = [
        {"text_hash": "abc"},
        {"text_hash": "abc"},
        {"text_hash": "def"},
    ]
    assert duplicate_hash_count(candidates) == 1


def test_uncertain_parse_flags_set_when_title_missing():
    record = make_parent_record("Dieu 1.\nNoi dung ngan.")
    candidates, warnings, rejected = derive_candidates_from_document(record)
    assert rejected is None
    assert candidates[0]["uncertain_parse"] is True
    assert "article_title_missing" in candidates[0]["parse_flags"]


def test_candidate_ground_truth_and_rag_flags_are_false():
    record = make_parent_record("Dieu 1. Pham vi dieu chinh\nNoi dung cua dieu 1.")
    candidates, warnings, rejected = derive_candidates_from_document(record)
    assert rejected is None
    assert candidates[0]["is_legal_ground_truth"] is False
    assert candidates[0]["approved_for_rag_index"] is False


def test_output_path_must_stay_inside_artifacts(tmp_path: Path):
    repo_like_root = tmp_path / "repo"
    artifacts = repo_like_root / "artifacts"
    input_dir = artifacts / "phase_2d_controlled_ingestion" / "uts_vlc"
    output_dir = repo_like_root / "outside"
    input_dir.mkdir(parents=True)
    import scripts.parse_uts_vlc_articles as cli

    original_root = cli.ROOT
    try:
        cli.ROOT = repo_like_root
        try:
            ensure_safe_output_paths(input_dir, output_dir, None)
            assert False, "Expected ValueError for output outside artifacts"
        except ValueError:
            assert True
    finally:
        cli.ROOT = original_root


def test_cli_refuses_output_paths_outside_artifacts(tmp_path: Path):
    repo_like_root = tmp_path / "repo"
    input_dir = repo_like_root / "artifacts" / "phase_2d_controlled_ingestion" / "uts_vlc"
    input_dir.mkdir(parents=True)
    for name, content in {
        "sample_normalized.jsonl": json.dumps(make_parent_record("Dieu 1. Pham vi\nNoi dung.")) + "\n",
        "provenance_manifest.json": "{}",
        "quality_report.json": "{}",
    }.items():
        (input_dir / name).write_text(content, encoding="utf-8")

    import scripts.parse_uts_vlc_articles as cli

    original_root = cli.ROOT
    try:
        cli.ROOT = repo_like_root
        exit_code = main(
            [
                "--input-dir",
                str(input_dir),
                "--output-dir",
                str(repo_like_root / "bad-output"),
            ]
        )
        assert exit_code != 0
    finally:
        cli.ROOT = original_root


def test_cli_writes_outputs_under_safe_artifacts_path(tmp_path: Path):
    repo_like_root = tmp_path / "repo"
    input_dir = repo_like_root / "artifacts" / "phase_2d_controlled_ingestion" / "uts_vlc"
    output_dir = repo_like_root / "artifacts" / "phase_2f_uts_article_candidates"
    report_out = repo_like_root / "artifacts" / "phase_2f_uts_article_parse_report.json"
    input_dir.mkdir(parents=True)

    record = make_parent_record(
        "Dieu 1. Pham vi dieu chinh\nNoi dung cua dieu 1.\n\nDieu 2. Giai thich tu ngu\nNoi dung cua dieu 2."
    )
    (input_dir / "sample_normalized.jsonl").write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
    (input_dir / "provenance_manifest.json").write_text("{}", encoding="utf-8")
    (input_dir / "quality_report.json").write_text("{}", encoding="utf-8")

    import scripts.parse_uts_vlc_articles as cli

    original_root = cli.ROOT
    try:
        cli.ROOT = repo_like_root
        exit_code = main(
            [
                "--input-dir",
                str(input_dir),
                "--output-dir",
                str(output_dir),
                "--report-out",
                str(report_out),
            ]
        )
        assert exit_code == 0
        assert (output_dir / "article_candidates.jsonl").exists()
        assert (output_dir / "parse_report.json").exists()
        assert (output_dir / "rejected_documents.jsonl").exists()
        assert (output_dir / "parse_warnings.jsonl").exists()
        report = json.loads((output_dir / "parse_report.json").read_text(encoding="utf-8"))
        assert report["status"] in {"PASS", "PASS WITH RISKS"}
    finally:
        cli.ROOT = original_root


def test_cli_fails_closed_when_parent_provenance_missing(tmp_path: Path):
    repo_like_root = tmp_path / "repo"
    input_dir = repo_like_root / "artifacts" / "phase_2d_controlled_ingestion" / "uts_vlc"
    output_dir = repo_like_root / "artifacts" / "phase_2f_uts_article_candidates"
    input_dir.mkdir(parents=True)

    record = make_parent_record("Dieu 1. Pham vi dieu chinh\nNoi dung cua dieu 1.")
    record["license"] = ""
    (input_dir / "sample_normalized.jsonl").write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
    (input_dir / "provenance_manifest.json").write_text("{}", encoding="utf-8")
    (input_dir / "quality_report.json").write_text("{}", encoding="utf-8")

    import scripts.parse_uts_vlc_articles as cli

    original_root = cli.ROOT
    try:
        cli.ROOT = repo_like_root
        exit_code = main(
            [
                "--input-dir",
                str(input_dir),
                "--output-dir",
                str(output_dir),
            ]
        )
        assert exit_code != 0
        assert not (output_dir / "article_candidates.jsonl").exists()
        report = json.loads((output_dir / "parse_report.json").read_text(encoding="utf-8"))
        assert report["blocked"] is True
        assert "license" in report["blocked_missing_provenance_fields"]
    finally:
        cli.ROOT = original_root
