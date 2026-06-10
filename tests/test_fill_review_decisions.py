from __future__ import annotations

import csv
from pathlib import Path

import pytest

import scripts.fill_review_decisions as cli
from vilegal.ingestion.review_results import validate_review_results_file


def make_template_row(**overrides: str) -> dict[str, str]:
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
        "reviewer_id": "",
        "review_date": "",
        "decision_label": "",
        "confidence": "",
        "notes": "",
        "legal_ground_truth_approved": "False",
        "rag_index_approved": "False",
    }
    row.update(overrides)
    return row


def write_csv(path: Path, rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def base_args(template: Path, output: Path) -> list[str]:
    return [
        "--template",
        str(template),
        "--output",
        str(output),
        "--reviewer-id",
        "Dat071104",
        "--review-date",
        "2026-06-10",
        "--decision-label",
        "accept_for_later_corpus_candidate",
        "--confidence",
        "medium",
        "--notes",
        "Human bulk-filled after manual sample review.",
        "--i-confirm-human-reviewed",
        "--i-understand-not-legal-ground-truth",
        "--i-understand-not-rag-approved",
    ]


def with_repo_root(repo: Path):
    class _RepoRoot:
        def __enter__(self) -> None:
            self.original_root = cli.ROOT
            cli.ROOT = repo

        def __exit__(self, exc_type, exc, tb) -> None:
            cli.ROOT = self.original_root

    return _RepoRoot()


def test_missing_confirmation_flags_do_not_write_output(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    template = write_csv(repo / "artifacts" / "template.csv", [make_template_row()])
    output = repo / "artifacts" / "completed.csv"
    args = base_args(template, output)
    args.remove("--i-understand-not-rag-approved")

    with with_repo_root(repo):
        exit_code = cli.main(args)

    assert exit_code == 2
    assert not output.exists()


def test_output_path_outside_artifacts_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    template = write_csv(repo / "artifacts" / "template.csv", [make_template_row()])
    output = repo / "outside" / "completed.csv"

    with with_repo_root(repo):
        exit_code = cli.main(base_args(template, output))

    assert exit_code == 2
    assert not output.exists()


def test_existing_output_requires_overwrite_flag(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    template = write_csv(repo / "artifacts" / "template.csv", [make_template_row()])
    output = write_csv(repo / "artifacts" / "completed.csv", [make_template_row(candidate_id="old")])
    original = output.read_text(encoding="utf-8")

    with with_repo_root(repo):
        exit_code = cli.main(base_args(template, output))

    assert exit_code == 2
    assert output.read_text(encoding="utf-8") == original


def test_valid_bulk_fill_writes_all_rows_and_preserves_candidate_id(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    template = write_csv(
        repo / "artifacts" / "template.csv",
        [
            make_template_row(candidate_id="candidate-001"),
            make_template_row(candidate_id="candidate-XYZ", review_sample_id="phase2h-keep-002-sample"),
        ],
    )
    output = repo / "artifacts" / "completed.csv"

    with with_repo_root(repo):
        exit_code = cli.main(base_args(template, output))

    rows = load_csv(output)
    assert exit_code == 0
    assert len(rows) == 2
    assert [row["candidate_id"] for row in rows] == ["candidate-001", "candidate-XYZ"]
    assert all(row["reviewer_id"] == "Dat071104" for row in rows)
    assert all(row["review_date"] == "2026-06-10" for row in rows)
    assert all(row["decision_label"] == "accept_for_later_corpus_candidate" for row in rows)
    assert all(row["confidence"] == "medium" for row in rows)


def test_flags_are_always_written_false_and_notes_are_preserved(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    template = write_csv(
        repo / "artifacts" / "template.csv",
        [
            make_template_row(
                legal_ground_truth_approved="true",
                rag_index_approved="yes",
                notes="stale note",
            )
        ],
    )
    output = repo / "artifacts" / "completed.csv"
    notes = (
        "Candidate accepted only for later corpus-candidate review; "
        "not legal ground truth and not RAG-approved."
    )
    args = base_args(template, output)
    args[args.index("Human bulk-filled after manual sample review.")]=notes

    with with_repo_root(repo):
        exit_code = cli.main(args)

    rows = load_csv(output)
    assert exit_code == 0
    assert rows[0]["notes"] == notes
    assert rows[0]["legal_ground_truth_approved"] == "false"
    assert rows[0]["rag_index_approved"] == "false"


def test_invalid_decision_label_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    template = write_csv(repo / "artifacts" / "template.csv", [make_template_row()])
    output = repo / "artifacts" / "completed.csv"
    args = base_args(template, output)
    args[args.index("accept_for_later_corpus_candidate")] = "bad_label"

    with with_repo_root(repo), pytest.raises(SystemExit) as exc_info:
        cli.main(args)

    assert exc_info.value.code == 2
    assert not output.exists()


def test_invalid_confidence_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    template = write_csv(repo / "artifacts" / "template.csv", [make_template_row()])
    output = repo / "artifacts" / "completed.csv"
    args = base_args(template, output)
    args[args.index("medium")] = "certain"

    with with_repo_root(repo), pytest.raises(SystemExit) as exc_info:
        cli.main(args)

    assert exc_info.value.code == 2
    assert not output.exists()


def test_overwrite_replaces_existing_output_only_with_flag(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    template = write_csv(repo / "artifacts" / "template.csv", [make_template_row(candidate_id="candidate-new")])
    output = write_csv(repo / "artifacts" / "completed.csv", [make_template_row(candidate_id="candidate-old")])
    args = base_args(template, output) + ["--overwrite"]

    with with_repo_root(repo):
        exit_code = cli.main(args)

    rows = load_csv(output)
    assert exit_code == 0
    assert len(rows) == 1
    assert rows[0]["candidate_id"] == "candidate-new"


def test_generated_csv_passes_phase2i_review_validation(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    template = write_csv(
        repo / "artifacts" / "template.csv",
        [
            make_template_row(candidate_id="candidate-001"),
            make_template_row(candidate_id="candidate-002", review_sample_id="phase2h-keep-002-sample"),
        ],
    )
    output = repo / "artifacts" / "completed.csv"

    with with_repo_root(repo):
        exit_code = cli.main(base_args(template, output))

    valid_rows, report = validate_review_results_file(output)

    assert exit_code == 0
    assert len(valid_rows) == 2
    assert report.safety_verdict == "PASS"
