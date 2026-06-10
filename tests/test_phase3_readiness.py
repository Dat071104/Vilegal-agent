from __future__ import annotations

import json
from pathlib import Path

import scripts.check_phase3_readiness as cli
from vilegal.ingestion.readiness_gate import BLOCKED_STATUS, check_phase3_readiness


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def make_manifest_row(**overrides) -> dict:
    row = {
        "candidate_id": "candidate-001",
        "parent_record_id": "parent-001",
        "source_dataset": "undertheseanlp/UTS_VLC",
        "source_id": "LAW-001",
        "source_url": "https://example.invalid/doc-1",
        "license": "MIT",
        "title": "Luat mau",
        "article_number": 1,
        "article_title": "Dieu 1",
        "text_hash": "hash-001",
        "parser_version": "phase_2f_v1",
        "filter_version": "phase_2g_v1",
        "reviewer_id": "reviewer-a",
        "review_date": "2026-06-10",
        "decision_label": "accept_for_later_corpus_candidate",
        "confidence": "medium",
        "review_scope": "phase_2h_sample_only",
        "approval_scope": "later_corpus_candidate_review_only",
        "is_legal_ground_truth": False,
        "approved_for_rag_index": False,
        "approved_for_qa_generation": False,
        "approved_for_fine_tuning": False,
        "phase3_ready": False,
    }
    row.update(overrides)
    return row


def make_manifest_report() -> dict:
    return {
        "metrics": {
            "manifest_records_written": 1,
            "unique_parent_documents": 1,
        }
    }


def write_docs(repo: Path, *, include_sample_limit: bool = True, include_bulk_limit: bool = True) -> None:
    docs_dir = repo / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    write_json(repo / "artifacts" / "placeholder.json", {})
    (docs_dir / "ATTRIBUTION.md").write_text("Attribution requirements.", encoding="utf-8")
    (docs_dir / "DATA_USE_POLICY.md").write_text("Data use policy.", encoding="utf-8")
    phase2j = ["Phase 2J audit doc."]
    phase2k = ["Phase 2K manifest doc."]
    if include_sample_limit:
        phase2j.append("The completed review covers the Phase 2H sample only and is not the full corpus.")
        phase2k.append("This manifest remains sample-scope only and is not the full corpus.")
    if include_bulk_limit:
        phase2j.append("The completed review is bulk-filled after human confirmation.")
    (docs_dir / "PHASE_2J_REVIEW_RESULTS_AUDIT.md").write_text("\n".join(phase2j), encoding="utf-8")
    (docs_dir / "PHASE_2K_CORPUS_CANDIDATE_MANIFEST.md").write_text("\n".join(phase2k), encoding="utf-8")


def seed_manifest_dir(repo: Path, *, row: dict | None = None) -> Path:
    manifest_dir = repo / "artifacts" / "phase_2k_corpus_candidate_manifest"
    write_json(manifest_dir / "manifest_report.json", make_manifest_report())
    write_jsonl(manifest_dir / "corpus_candidate_manifest.jsonl", [row or make_manifest_row()])
    return manifest_dir


def with_repo_root(repo: Path):
    class _RepoRoot:
        def __enter__(self) -> None:
            self.original_root = cli.ROOT
            cli.ROOT = repo

        def __exit__(self, exc_type, exc, tb) -> None:
            cli.ROOT = self.original_root

    return _RepoRoot()


def test_valid_readiness_gate_returns_pass_with_risks(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_docs(repo)
    manifest_dir = seed_manifest_dir(repo)

    report = check_phase3_readiness(
        manifest_dir=manifest_dir,
        attribution_path=repo / "docs" / "ATTRIBUTION.md",
        data_use_policy_path=repo / "docs" / "DATA_USE_POLICY.md",
        phase2j_doc_path=repo / "docs" / "PHASE_2J_REVIEW_RESULTS_AUDIT.md",
        phase2k_doc_path=repo / "docs" / "PHASE_2K_CORPUS_CANDIDATE_MANIFEST.md",
    )

    assert report.readiness_verdict == "PASS WITH RISKS"
    assert report.corpus_candidate_manifest_ready is True
    assert report.phase3_scaffold_ready is True
    assert report.qa_generation_ready is False
    assert report.fine_tuning_ready is False
    assert report.rag_indexing_ready is False


def test_missing_manifest_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_docs(repo)
    manifest_dir = repo / "artifacts" / "phase_2k_corpus_candidate_manifest"

    report = check_phase3_readiness(
        manifest_dir=manifest_dir,
        attribution_path=repo / "docs" / "ATTRIBUTION.md",
        data_use_policy_path=repo / "docs" / "DATA_USE_POLICY.md",
        phase2j_doc_path=repo / "docs" / "PHASE_2J_REVIEW_RESULTS_AUDIT.md",
        phase2k_doc_path=repo / "docs" / "PHASE_2K_CORPUS_CANDIDATE_MANIFEST.md",
    )

    assert report.readiness_verdict == "FAIL"
    assert report.corpus_candidate_manifest_ready is False


def test_true_downstream_flags_fail_closed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_docs(repo)
    manifest_dir = seed_manifest_dir(repo, row=make_manifest_row(approved_for_rag_index=True))

    report = check_phase3_readiness(
        manifest_dir=manifest_dir,
        attribution_path=repo / "docs" / "ATTRIBUTION.md",
        data_use_policy_path=repo / "docs" / "DATA_USE_POLICY.md",
        phase2j_doc_path=repo / "docs" / "PHASE_2J_REVIEW_RESULTS_AUDIT.md",
        phase2k_doc_path=repo / "docs" / "PHASE_2K_CORPUS_CANDIDATE_MANIFEST.md",
    )

    assert report.readiness_verdict == "FAIL"
    assert report.checks.rag_index_approved_true_count == 1


def test_missing_limit_documentation_blocks_scaffold_planning(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_docs(repo, include_sample_limit=False)
    manifest_dir = seed_manifest_dir(repo)

    report = check_phase3_readiness(
        manifest_dir=manifest_dir,
        attribution_path=repo / "docs" / "ATTRIBUTION.md",
        data_use_policy_path=repo / "docs" / "DATA_USE_POLICY.md",
        phase2j_doc_path=repo / "docs" / "PHASE_2J_REVIEW_RESULTS_AUDIT.md",
        phase2k_doc_path=repo / "docs" / "PHASE_2K_CORPUS_CANDIDATE_MANIFEST.md",
    )

    assert report.readiness_verdict == BLOCKED_STATUS
    assert report.phase3_scaffold_ready is False


def test_cli_rejects_report_outside_artifacts(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_docs(repo)
    manifest_dir = seed_manifest_dir(repo)

    with with_repo_root(repo):
        exit_code = cli.main(
            [
                "--manifest-dir",
                str(manifest_dir),
                "--report-out",
                str(repo / "outside" / "report.json"),
            ]
        )

    assert exit_code == 2


def test_license_fields_required_for_manifest_readiness(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_docs(repo)
    manifest_dir = seed_manifest_dir(repo, row=make_manifest_row(license=""))

    report = check_phase3_readiness(
        manifest_dir=manifest_dir,
        attribution_path=repo / "docs" / "ATTRIBUTION.md",
        data_use_policy_path=repo / "docs" / "DATA_USE_POLICY.md",
        phase2j_doc_path=repo / "docs" / "PHASE_2J_REVIEW_RESULTS_AUDIT.md",
        phase2k_doc_path=repo / "docs" / "PHASE_2K_CORPUS_CANDIDATE_MANIFEST.md",
    )

    assert report.corpus_candidate_manifest_ready is False
    assert report.readiness_verdict == BLOCKED_STATUS
