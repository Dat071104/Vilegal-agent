from __future__ import annotations

import json
from pathlib import Path

from scripts.build_phase2h_review_pack import main
from vilegal.ingestion.review_sampler import build_review_pack


def make_record(
    input_index: int,
    decision: str,
    *,
    parent_record_id: str,
    article_hash: str,
    candidate_id: str | None = None,
    filter_reasons: list[str] | None = None,
    risk_flags: list[str] | None = None,
    parent_warning: bool = False,
    duplicate_of: str | None = None,
) -> dict:
    text = f"Dieu {input_index}. Noi dung " + ("word " * 24)
    return {
        "parent_record_id": parent_record_id,
        "source_dataset": "undertheseanlp/UTS_VLC",
        "source_id": f"LAW-{input_index:03d}",
        "source_url": "https://example.invalid/doc",
        "license": "MIT",
        "retrieved_at": "2026-06-10T00:00:00Z",
        "title": f"Title {input_index}",
        "article_number": input_index,
        "article_title": f"Article {input_index}",
        "chunk_index": 0,
        "text": text,
        "text_hash": article_hash,
        "parser_version": "phase_2f_v1",
        "parse_flags": [],
        "uncertain_parse": False,
        "is_legal_ground_truth": False,
        "approved_for_rag_index": False,
        "input_index": input_index,
        "article_hash": article_hash,
        "candidate_id": candidate_id or f"candidate-{input_index:03d}",
        "text_char_count": len(text.strip()),
        "text_word_count": len(text.strip().split()),
        "parent_document_warning_codes": ["preamble_before_first_article"] if parent_warning else [],
        "parent_document_warning_messages": ["warning"] if parent_warning else [],
        "risk_flags": list(risk_flags or []),
        "filter_reasons": list(filter_reasons or [decision]),
        "duplicate_of": duplicate_of,
        "filter_decision": decision,
    }


def make_phase2g_records() -> list[dict]:
    return [
        make_record(0, "keep_candidate_for_human_review", parent_record_id="parent-a", article_hash="hash-a"),
        make_record(1, "keep_candidate_for_human_review", parent_record_id="parent-b", article_hash="hash-b", parent_warning=True),
        make_record(2, "keep_candidate_for_human_review", parent_record_id="parent-c", article_hash="hash-c"),
        make_record(3, "keep_candidate_for_human_review", parent_record_id="parent-d", article_hash="hash-d"),
        make_record(4, "keep_candidate_for_human_review", parent_record_id="parent-e", article_hash="hash-dup1", candidate_id="dup-1"),
        make_record(
            5,
            "reject_duplicate_hash",
            parent_record_id="parent-f",
            article_hash="hash-dup1",
            candidate_id="dup-1",
            filter_reasons=["reject_duplicate_hash"],
            risk_flags=["duplicate_hash_loser"],
            duplicate_of="dup-1",
        ),
        make_record(6, "keep_candidate_for_human_review", parent_record_id="parent-g", article_hash="hash-dup2", candidate_id="dup-2", parent_warning=True),
        make_record(
            7,
            "reject_duplicate_hash",
            parent_record_id="parent-h",
            article_hash="hash-dup2",
            candidate_id="dup-2",
            filter_reasons=["reject_duplicate_hash"],
            risk_flags=["duplicate_hash_loser"],
            duplicate_of="dup-2",
        ),
        make_record(
            8,
            "needs_review_marker_uncertainty",
            parent_record_id="parent-i",
            article_hash="hash-i",
            filter_reasons=["needs_review_marker_uncertainty"],
            risk_flags=["marker_uncertainty"],
        ),
        make_record(
            9,
            "needs_review_suspicious_length",
            parent_record_id="parent-j",
            article_hash="hash-j",
            filter_reasons=["needs_review_suspicious_length"],
            risk_flags=["suspicious_length_text"],
        ),
        make_record(
            10,
            "needs_review_suspicious_length",
            parent_record_id="parent-k",
            article_hash="hash-k",
            filter_reasons=["needs_review_suspicious_length"],
            risk_flags=["suspicious_length_text"],
            parent_warning=True,
        ),
        make_record(
            11,
            "needs_review_marker_uncertainty",
            parent_record_id="parent-l",
            article_hash="hash-l",
            filter_reasons=["needs_review_marker_uncertainty"],
            risk_flags=["marker_uncertainty"],
        ),
        make_record(
            12,
            "reject_near_empty",
            parent_record_id="parent-m",
            article_hash="hash-m",
            filter_reasons=["reject_near_empty"],
            risk_flags=["near_empty_text"],
        ),
        make_record(
            13,
            "reject_near_empty",
            parent_record_id="parent-n",
            article_hash="hash-n",
            filter_reasons=["reject_near_empty"],
            risk_flags=["near_empty_text"],
        ),
        make_record(14, "keep_candidate_for_human_review", parent_record_id="parent-o", article_hash="hash-o"),
    ]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def write_phase2g_fixture(repo: Path, records: list[dict]) -> Path:
    input_dir = repo / "artifacts" / "phase_2g_uts_filtering"
    input_dir.mkdir(parents=True, exist_ok=True)
    rejected = [record for record in records if str(record["filter_decision"]).startswith("reject_")]
    needs_review = [record for record in records if str(record["filter_decision"]).startswith("needs_review_")]
    duplicate_group_sizes = {"hash-dup1": 2, "hash-dup2": 2}

    write_jsonl(input_dir / "filtered_candidates.jsonl", records)
    write_jsonl(input_dir / "rejected_candidates.jsonl", rejected)
    write_jsonl(input_dir / "needs_review_candidates.jsonl", needs_review)
    (input_dir / "filter_report.json").write_text(
        json.dumps(
            {
                "filter_version": "phase_2g_v1",
                "source_manifest_path": str(repo / "artifacts" / "phase_2d_controlled_ingestion" / "uts_vlc" / "provenance_manifest.json"),
                "metrics": {
                    "total_input_candidates": len(records),
                    "total_rejected": len(rejected),
                    "total_needs_review": len(needs_review),
                },
                "duplicate_group_sizes": duplicate_group_sizes,
            }
        ),
        encoding="utf-8",
    )
    return input_dir


def ensure_rubric(repo: Path) -> Path:
    rubric_path = repo / "docs" / "MANUAL_REVIEW_RUBRIC.md"
    rubric_path.parent.mkdir(parents=True, exist_ok=True)
    rubric_path.write_text("# rubric\n", encoding="utf-8")
    return rubric_path


def test_deterministic_sampling_same_seed_same_ids(tmp_path: Path):
    repo = tmp_path / "repo"
    records = make_phase2g_records()
    input_dir = write_phase2g_fixture(repo, records)
    rubric = ensure_rubric(repo)

    result_a = build_review_pack(
        input_dir=input_dir,
        output_dir=repo / "artifacts" / "phase_2h_a",
        sample_size=12,
        seed=42,
        rubric_path=rubric,
    )
    result_b = build_review_pack(
        input_dir=input_dir,
        output_dir=repo / "artifacts" / "phase_2h_b",
        sample_size=12,
        seed=42,
        rubric_path=rubric,
    )

    assert [row["review_sample_id"] for row in result_a["review_sample"]] == [
        row["review_sample_id"] for row in result_b["review_sample"]
    ]
    assert result_a["sampling_report"]["sampled_by_bucket"] == result_b["sampling_report"]["sampled_by_bucket"]


def test_stratified_sampling_represents_major_buckets_when_available(tmp_path: Path):
    repo = tmp_path / "repo"
    input_dir = write_phase2g_fixture(repo, make_phase2g_records())
    rubric = ensure_rubric(repo)

    result = build_review_pack(
        input_dir=input_dir,
        output_dir=repo / "artifacts" / "phase_2h_review_pack",
        sample_size=12,
        seed=42,
        rubric_path=rubric,
    )
    buckets = result["sampling_report"]["sampled_by_bucket"]

    assert buckets["keep_candidate_for_human_review"] > 0
    assert buckets["needs_review"] > 0
    assert buckets["rejected"] > 0


def test_bucket_shortfall_reported_when_bucket_has_fewer_records_than_requested(tmp_path: Path):
    repo = tmp_path / "repo"
    records = [record for record in make_phase2g_records() if record["filter_decision"] != "reject_near_empty"]
    input_dir = write_phase2g_fixture(repo, records)
    rubric = ensure_rubric(repo)

    result = build_review_pack(
        input_dir=input_dir,
        output_dir=repo / "artifacts" / "phase_2h_review_pack",
        sample_size=40,
        seed=42,
        rubric_path=rubric,
    )

    assert result["sampling_report"]["bucket_shortfalls"]["rejected"] > 0


def test_safety_flags_remain_false_for_all_output_records(tmp_path: Path):
    repo = tmp_path / "repo"
    input_dir = write_phase2g_fixture(repo, make_phase2g_records())
    rubric = ensure_rubric(repo)

    result = build_review_pack(
        input_dir=input_dir,
        output_dir=repo / "artifacts" / "phase_2h_review_pack",
        sample_size=12,
        seed=42,
        rubric_path=rubric,
    )

    assert all(record["approved_for_rag_index"] is False for record in result["review_sample"])
    assert all(record["is_legal_ground_truth"] is False for record in result["review_sample"])


def test_output_sample_records_include_required_review_fields(tmp_path: Path):
    repo = tmp_path / "repo"
    input_dir = write_phase2g_fixture(repo, make_phase2g_records())
    rubric = ensure_rubric(repo)

    result = build_review_pack(
        input_dir=input_dir,
        output_dir=repo / "artifacts" / "phase_2h_review_pack",
        sample_size=12,
        seed=42,
        rubric_path=rubric,
    )

    required = {
        "review_sample_id",
        "candidate_id",
        "parent_record_id",
        "source_dataset",
        "source_id",
        "source_url",
        "license",
        "title",
        "article_number",
        "article_title",
        "filter_decision",
        "filter_reasons",
        "risk_flags",
        "text_length",
        "text_hash",
        "parser_version",
        "filter_version",
        "sampling_seed",
        "sampling_bucket",
        "is_legal_ground_truth",
        "approved_for_rag_index",
    }
    assert required.issubset(result["review_sample"][0].keys())


def test_cli_refuses_output_path_outside_artifacts(tmp_path: Path):
    repo = tmp_path / "repo"
    input_dir = write_phase2g_fixture(repo, make_phase2g_records())
    ensure_rubric(repo)

    import scripts.build_phase2h_review_pack as cli

    original_root = cli.ROOT
    try:
        cli.ROOT = repo
        exit_code = main(
            [
                "--input-dir",
                str(input_dir),
                "--output-dir",
                str(repo / "outside"),
                "--sample-size",
                "12",
                "--seed",
                "42",
            ]
        )
        assert exit_code != 0
    finally:
        cli.ROOT = original_root


def test_cli_fails_safely_when_required_inputs_are_missing(tmp_path: Path):
    repo = tmp_path / "repo"
    missing_input = repo / "artifacts" / "phase_2g_uts_filtering"

    import scripts.build_phase2h_review_pack as cli

    original_root = cli.ROOT
    try:
        cli.ROOT = repo
        exit_code = main(
            [
                "--input-dir",
                str(missing_input),
                "--output-dir",
                str(repo / "artifacts" / "phase_2h_review_pack"),
            ]
        )
        assert exit_code != 0
    finally:
        cli.ROOT = original_root


def test_phase2h_docs_do_not_embed_large_candidate_text() -> None:
    docs = [
        Path("docs/PHASE_2H_MANUAL_REVIEW_PACK.md"),
        Path("docs/MANUAL_REVIEW_RUBRIC.md"),
    ]
    for path in docs:
        content = path.read_text(encoding="utf-8")
        assert '"text": "' not in content
        assert max(len(line) for line in content.splitlines()) < 240


def test_sampling_report_reconciles_total_sampled_with_bucket_sum(tmp_path: Path):
    repo = tmp_path / "repo"
    input_dir = write_phase2g_fixture(repo, make_phase2g_records())
    rubric = ensure_rubric(repo)

    result = build_review_pack(
        input_dir=input_dir,
        output_dir=repo / "artifacts" / "phase_2h_review_pack",
        sample_size=12,
        seed=42,
        rubric_path=rubric,
    )

    assert result["sampling_report"]["total_sampled"] == sum(result["sampling_report"]["sampled_by_bucket"].values())


def test_duplicate_and_suspicious_buckets_are_sampled_when_available(tmp_path: Path):
    repo = tmp_path / "repo"
    input_dir = write_phase2g_fixture(repo, make_phase2g_records())
    rubric = ensure_rubric(repo)

    result = build_review_pack(
        input_dir=input_dir,
        output_dir=repo / "artifacts" / "phase_2h_review_pack",
        sample_size=12,
        seed=42,
        rubric_path=rubric,
    )

    assert result["sampling_report"]["sampled_duplicate_examples"] > 0
    assert result["sampling_report"]["sampled_suspicious_length_examples"] > 0
