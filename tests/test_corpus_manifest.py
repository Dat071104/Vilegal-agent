from __future__ import annotations

import csv
import json
from pathlib import Path

import scripts.build_corpus_candidate_manifest as cli
from vilegal.ingestion.corpus_manifest import build_corpus_candidate_manifest


def write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def write_csv(path: Path, rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def make_accepted_row(candidate_id: str) -> dict:
    return {
        "candidate_id": candidate_id,
        "bucket": "accepted_for_later_review",
        "consensus_label": "accept_for_later_corpus_candidate",
        "adjudication_status": "consensus",
        "review_count": 1,
        "reviewer_ids": ["reviewer-a"],
        "legal_ground_truth_approved": False,
        "rag_index_approved": False,
        "phase3_ready": False,
    }


def make_review_sample_row(candidate_id: str, **overrides) -> dict:
    row = {
        "review_sample_id": f"phase2h-keep-{candidate_id}",
        "candidate_id": candidate_id,
        "parent_record_id": f"parent-{candidate_id}",
        "source_dataset": "undertheseanlp/UTS_VLC",
        "source_id": f"SRC-{candidate_id}",
        "source_url": "https://example.invalid/legal-doc",
        "license": "MIT",
        "title": "Luat mau",
        "article_number": 1,
        "article_title": "Dieu 1",
        "text_hash": f"hash-{candidate_id}",
        "parser_version": "phase_2f_v1",
        "filter_version": "phase_2g_v1",
        "sampling_bucket": "keep_candidate_for_human_review",
        "filter_decision": "keep_candidate_for_human_review",
        "is_legal_ground_truth": False,
        "approved_for_rag_index": False,
    }
    row.update(overrides)
    return row


def make_completed_review_row(candidate_id: str, **overrides) -> dict[str, str]:
    row = {
        "review_sample_id": f"phase2h-keep-{candidate_id}",
        "candidate_id": candidate_id,
        "parent_record_id": f"parent-{candidate_id}",
        "source_dataset": "undertheseanlp/UTS_VLC",
        "source_id": f"SRC-{candidate_id}",
        "source_url": "https://example.invalid/legal-doc",
        "license": "MIT",
        "title": "Luat mau",
        "article_number": "1",
        "article_title": "Dieu 1",
        "filter_decision": "keep_candidate_for_human_review",
        "sampling_bucket": "keep_candidate_for_human_review",
        "reviewer_id": "reviewer-a",
        "review_date": "2026-06-10",
        "decision_label": "accept_for_later_corpus_candidate",
        "confidence": "medium",
        "notes": "Sample-only later corpus candidate.",
        "legal_ground_truth_approved": "false",
        "rag_index_approved": "false",
    }
    row.update(overrides)
    return row


def make_filter_row(candidate_id: str, **overrides) -> dict:
    row = {
        "candidate_id": candidate_id,
        "parent_record_id": f"parent-{candidate_id}",
        "source_dataset": "undertheseanlp/UTS_VLC",
        "source_id": f"SRC-{candidate_id}",
        "source_url": "https://example.invalid/legal-doc",
        "license": "MIT",
        "title": "Luat mau",
        "article_number": 1,
        "article_title": "Dieu 1",
        "text_hash": f"hash-{candidate_id}",
        "article_hash": f"hash-{candidate_id}",
        "parser_version": "phase_2f_v1",
        "filter_version": "phase_2g_v1",
        "filter_decision": "keep_candidate_for_human_review",
    }
    row.update(overrides)
    return row


def seed_phase2k_dirs(repo: Path) -> tuple[Path, Path, Path, Path]:
    review_audit_dir = repo / "artifacts" / "phase_2j_review_results_audit"
    review_pack_dir = repo / "artifacts" / "phase_2h_manual_review_pack"
    filter_dir = repo / "artifacts" / "phase_2g_uts_filtering"
    output_dir = repo / "artifacts" / "phase_2k_corpus_candidate_manifest"

    write_jsonl(review_audit_dir / "accepted_candidate_ids_for_later_review.jsonl", [make_accepted_row("candidate-001")])
    write_jsonl(review_pack_dir / "review_sample.jsonl", [make_review_sample_row("candidate-001")])
    write_csv(review_pack_dir / "reviewer_decisions_completed.csv", [make_completed_review_row("candidate-001")])
    write_jsonl(filter_dir / "filtered_candidates.jsonl", [make_filter_row("candidate-001")])
    write_jsonl(filter_dir / "needs_review_candidates.jsonl", [])
    write_jsonl(filter_dir / "rejected_candidates.jsonl", [])
    return review_audit_dir, review_pack_dir, filter_dir, output_dir


def with_repo_root(repo: Path):
    class _RepoRoot:
        def __enter__(self) -> None:
            self.original_root = cli.ROOT
            cli.ROOT = repo

        def __exit__(self, exc_type, exc, tb) -> None:
            cli.ROOT = self.original_root

    return _RepoRoot()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def test_valid_manifest_build(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    review_audit_dir, review_pack_dir, filter_dir, output_dir = seed_phase2k_dirs(repo)

    report, outputs = build_corpus_candidate_manifest(
        review_audit_dir=review_audit_dir,
        review_pack_dir=review_pack_dir,
        filter_dir=filter_dir,
        output_dir=output_dir,
    )

    assert report.status == "PASS WITH RISKS"
    assert report.metrics.manifest_records_written == 1
    assert report.metrics.accepted_candidate_ids_input_count == 1
    assert report.metrics.counts_reconcile is True
    assert outputs["rejected_from_manifest"] == []
    assert outputs["unresolved_from_manifest"] == []
    manifest_rows = load_jsonl(output_dir / "corpus_candidate_manifest.jsonl")
    assert manifest_rows[0]["review_scope"] == "phase_2h_sample_only"
    assert manifest_rows[0]["approval_scope"] == "later_corpus_candidate_review_only"


def test_missing_accepted_id_file_fails_closed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    review_audit_dir = repo / "artifacts" / "phase_2j_review_results_audit"
    review_pack_dir = repo / "artifacts" / "phase_2h_manual_review_pack"
    filter_dir = repo / "artifacts" / "phase_2g_uts_filtering"
    output_dir = repo / "artifacts" / "phase_2k_corpus_candidate_manifest"

    write_jsonl(review_pack_dir / "review_sample.jsonl", [make_review_sample_row("candidate-001")])
    write_csv(review_pack_dir / "reviewer_decisions_completed.csv", [make_completed_review_row("candidate-001")])
    write_jsonl(filter_dir / "filtered_candidates.jsonl", [make_filter_row("candidate-001")])
    write_jsonl(filter_dir / "needs_review_candidates.jsonl", [])
    write_jsonl(filter_dir / "rejected_candidates.jsonl", [])

    try:
        build_corpus_candidate_manifest(
            review_audit_dir=review_audit_dir,
            review_pack_dir=review_pack_dir,
            filter_dir=filter_dir,
            output_dir=output_dir,
        )
    except FileNotFoundError as exc:
        assert "accepted_candidate_ids_for_later_review.jsonl" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError for missing accepted ID file.")


def test_missing_review_metadata_fails_closed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    review_audit_dir, review_pack_dir, filter_dir, output_dir = seed_phase2k_dirs(repo)
    write_csv(review_pack_dir / "reviewer_decisions_completed.csv", [make_completed_review_row("other-candidate")])

    report, _ = build_corpus_candidate_manifest(
        review_audit_dir=review_audit_dir,
        review_pack_dir=review_pack_dir,
        filter_dir=filter_dir,
        output_dir=output_dir,
    )

    assert report.status == "FAIL"
    assert report.metrics.missing_review_metadata_count == 1
    assert not (output_dir / "corpus_candidate_manifest.jsonl").exists()
    rejected_rows = load_jsonl(output_dir / "rejected_from_manifest.jsonl")
    assert rejected_rows[0]["candidate_id"] == "candidate-001"


def test_missing_filter_metadata_is_reported(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    review_audit_dir, review_pack_dir, filter_dir, output_dir = seed_phase2k_dirs(repo)
    write_jsonl(filter_dir / "filtered_candidates.jsonl", [])

    report, outputs = build_corpus_candidate_manifest(
        review_audit_dir=review_audit_dir,
        review_pack_dir=review_pack_dir,
        filter_dir=filter_dir,
        output_dir=output_dir,
    )

    assert report.status == "PASS WITH RISKS"
    assert report.metrics.missing_filter_metadata_count == 1
    assert report.metrics.manifest_records_written == 0
    assert outputs["unresolved_from_manifest"][0]["candidate_id"] == "candidate-001"


def test_review_sample_can_supply_manifest_versions_when_filter_row_omits_them(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    review_audit_dir, review_pack_dir, filter_dir, output_dir = seed_phase2k_dirs(repo)
    write_jsonl(
        filter_dir / "filtered_candidates.jsonl",
        [
            make_filter_row(
                "candidate-001",
                parser_version="",
                filter_version="",
            )
        ],
    )

    report, _ = build_corpus_candidate_manifest(
        review_audit_dir=review_audit_dir,
        review_pack_dir=review_pack_dir,
        filter_dir=filter_dir,
        output_dir=output_dir,
    )

    manifest_rows = load_jsonl(output_dir / "corpus_candidate_manifest.jsonl")
    assert report.status == "PASS WITH RISKS"
    assert report.metrics.manifest_records_written == 1
    assert manifest_rows[0]["parser_version"] == "phase_2f_v1"
    assert manifest_rows[0]["filter_version"] == "phase_2g_v1"


def test_output_path_outside_artifacts_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    review_audit_dir, review_pack_dir, filter_dir, _ = seed_phase2k_dirs(repo)
    output_dir = repo / "outside"

    with with_repo_root(repo):
        exit_code = cli.main(
            [
                "--review-audit-dir",
                str(review_audit_dir),
                "--review-pack-dir",
                str(review_pack_dir),
                "--filter-dir",
                str(filter_dir),
                "--output-dir",
                str(output_dir),
            ]
        )

    assert exit_code == 2


def test_all_approval_flags_forced_false(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    review_audit_dir, review_pack_dir, filter_dir, output_dir = seed_phase2k_dirs(repo)
    write_csv(
        review_pack_dir / "reviewer_decisions_completed.csv",
        [make_completed_review_row("candidate-001", legal_ground_truth_approved="true", rag_index_approved="true")],
    )

    report, _ = build_corpus_candidate_manifest(
        review_audit_dir=review_audit_dir,
        review_pack_dir=review_pack_dir,
        filter_dir=filter_dir,
        output_dir=output_dir,
    )

    assert report.status == "FAIL"
    assert report.metrics.legal_ground_truth_true_count == 0
    assert report.metrics.rag_index_approved_true_count == 0


def test_phase3_ready_false(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    review_audit_dir, review_pack_dir, filter_dir, output_dir = seed_phase2k_dirs(repo)

    report, _ = build_corpus_candidate_manifest(
        review_audit_dir=review_audit_dir,
        review_pack_dir=review_pack_dir,
        filter_dir=filter_dir,
        output_dir=output_dir,
    )

    manifest_rows = load_jsonl(output_dir / "corpus_candidate_manifest.jsonl")
    assert report.metrics.phase3_ready_true_count == 0
    assert manifest_rows[0]["phase3_ready"] is False


def test_counts_reconcile(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    review_audit_dir, review_pack_dir, filter_dir, output_dir = seed_phase2k_dirs(repo)
    write_jsonl(
        review_audit_dir / "accepted_candidate_ids_for_later_review.jsonl",
        [make_accepted_row("candidate-001"), make_accepted_row("candidate-002")],
    )
    write_jsonl(
        review_pack_dir / "review_sample.jsonl",
        [
            make_review_sample_row("candidate-001"),
            make_review_sample_row("candidate-002"),
        ],
    )
    write_csv(
        review_pack_dir / "reviewer_decisions_completed.csv",
        [
            make_completed_review_row("candidate-001"),
            make_completed_review_row("candidate-002"),
        ],
    )
    write_jsonl(
        filter_dir / "filtered_candidates.jsonl",
        [make_filter_row("candidate-001"), make_filter_row("candidate-002")],
    )

    report, _ = build_corpus_candidate_manifest(
        review_audit_dir=review_audit_dir,
        review_pack_dir=review_pack_dir,
        filter_dir=filter_dir,
        output_dir=output_dir,
    )

    assert report.metrics.manifest_records_written == 2
    assert report.metrics.counts_reconcile is True


def test_duplicate_accepted_ids_handled_deterministically(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    review_audit_dir, review_pack_dir, filter_dir, output_dir = seed_phase2k_dirs(repo)
    write_jsonl(
        review_audit_dir / "accepted_candidate_ids_for_later_review.jsonl",
        [
            make_accepted_row("candidate-001"),
            make_accepted_row("candidate-001"),
        ],
    )

    report, _ = build_corpus_candidate_manifest(
        review_audit_dir=review_audit_dir,
        review_pack_dir=review_pack_dir,
        filter_dir=filter_dir,
        output_dir=output_dir,
    )

    manifest_rows = load_jsonl(output_dir / "corpus_candidate_manifest.jsonl")
    assert report.metrics.accepted_candidate_ids_input_count == 2
    assert report.metrics.duplicate_accepted_candidate_ids_count == 1
    assert [row["candidate_id"] for row in manifest_rows] == ["candidate-001"]


def test_no_silent_dropping(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    review_audit_dir, review_pack_dir, filter_dir, output_dir = seed_phase2k_dirs(repo)
    write_jsonl(
        review_audit_dir / "accepted_candidate_ids_for_later_review.jsonl",
        [
            make_accepted_row("candidate-001"),
            make_accepted_row("candidate-002"),
        ],
    )
    write_jsonl(review_pack_dir / "review_sample.jsonl", [make_review_sample_row("candidate-001"), make_review_sample_row("candidate-002")])
    write_csv(review_pack_dir / "reviewer_decisions_completed.csv", [make_completed_review_row("candidate-001"), make_completed_review_row("candidate-002")])
    write_jsonl(filter_dir / "filtered_candidates.jsonl", [make_filter_row("candidate-001")])

    report, outputs = build_corpus_candidate_manifest(
        review_audit_dir=review_audit_dir,
        review_pack_dir=review_pack_dir,
        filter_dir=filter_dir,
        output_dir=output_dir,
    )

    assert report.metrics.manifest_records_written == 1
    assert report.metrics.unresolved_from_manifest_count == 1
    assert outputs["unresolved_from_manifest"][0]["candidate_id"] == "candidate-002"


def test_manifest_scope_is_sample_only(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    review_audit_dir, review_pack_dir, filter_dir, output_dir = seed_phase2k_dirs(repo)

    build_corpus_candidate_manifest(
        review_audit_dir=review_audit_dir,
        review_pack_dir=review_pack_dir,
        filter_dir=filter_dir,
        output_dir=output_dir,
    )

    manifest_json = load_json(output_dir / "corpus_candidate_manifest.json")
    assert manifest_json["records"][0]["review_scope"] == "phase_2h_sample_only"
    assert manifest_json["records"][0]["approval_scope"] == "later_corpus_candidate_review_only"


def test_synthetic_fixtures_are_not_legal_ground_truth(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    review_audit_dir, review_pack_dir, filter_dir, output_dir = seed_phase2k_dirs(repo)

    report, _ = build_corpus_candidate_manifest(
        review_audit_dir=review_audit_dir,
        review_pack_dir=review_pack_dir,
        filter_dir=filter_dir,
        output_dir=output_dir,
    )

    manifest_rows = load_jsonl(output_dir / "corpus_candidate_manifest.jsonl")
    assert report.metrics.legal_ground_truth_true_count == 0
    assert report.metrics.rag_index_approved_true_count == 0
    assert manifest_rows[0]["is_legal_ground_truth"] is False
    assert manifest_rows[0]["approved_for_rag_index"] is False
