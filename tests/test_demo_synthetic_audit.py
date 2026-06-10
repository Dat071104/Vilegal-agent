from __future__ import annotations

import json
from pathlib import Path

import scripts.audit_synthetic_demo_qa as audit_cli
import scripts.split_synthetic_demo_qa as split_cli
from vilegal.demo_synthetic.generator import generate_synthetic_demo_rows, write_jsonl


ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = ROOT / "data" / "synthetic_demo" / "sample_qa.jsonl"


def read_rows(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_rows(path: Path, rows: list[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def test_audit_passes_on_tracked_sample() -> None:
    summary = audit_cli.audit_jsonl_file(SAMPLE_PATH, min_rows=10)
    assert summary.status == "PASS"
    assert summary.total_rows == 10


def test_audit_fails_on_duplicate_ids(tmp_path: Path) -> None:
    rows = read_rows(SAMPLE_PATH)
    rows[1]["id"] = rows[0]["id"]
    path = write_rows(tmp_path / "duplicate_ids.jsonl", rows)
    summary = audit_cli.audit_jsonl_file(path, min_rows=10)
    assert summary.status == "FAIL"
    assert summary.duplicate_id_count == 1


def test_audit_fails_on_source_not_synthetic_demo(tmp_path: Path) -> None:
    rows = read_rows(SAMPLE_PATH)
    rows[0]["source"] = "real-corpus"
    path = write_rows(tmp_path / "bad_source.jsonl", rows)
    summary = audit_cli.audit_jsonl_file(path, min_rows=10)
    assert summary.status == "FAIL"
    assert summary.source_mismatch_count == 1


def test_audit_fails_on_legal_ground_truth_true(tmp_path: Path) -> None:
    rows = read_rows(SAMPLE_PATH)
    rows[0]["is_legal_ground_truth"] = True
    path = write_rows(tmp_path / "bad_truth.jsonl", rows)
    summary = audit_cli.audit_jsonl_file(path, min_rows=10)
    assert summary.status == "FAIL"
    assert summary.legal_ground_truth_true_count == 1


def test_audit_fails_on_approved_for_rag_index_true(tmp_path: Path) -> None:
    rows = read_rows(SAMPLE_PATH)
    rows[0]["approved_for_rag_index"] = True
    path = write_rows(tmp_path / "bad_rag.jsonl", rows)
    summary = audit_cli.audit_jsonl_file(path, min_rows=10)
    assert summary.status == "FAIL"
    assert summary.approved_for_rag_index_true_count == 1


def test_split_script_creates_train_validation_test_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "splits"
    exit_code = split_cli.main(
        [
            str(SAMPLE_PATH),
            "--output-dir",
            str(output_dir),
            "--seed",
            "42",
        ]
    )
    assert exit_code == 0
    assert (output_dir / "train.jsonl").is_file()
    assert (output_dir / "validation.jsonl").is_file()
    assert (output_dir / "test.jsonl").is_file()


def test_split_counts_sum_to_input_row_count(tmp_path: Path) -> None:
    output_dir = tmp_path / "splits"
    split_cli.main([str(SAMPLE_PATH), "--output-dir", str(output_dir), "--seed", "42"])
    total = sum(len(read_rows(output_dir / f"{name}.jsonl")) for name in ("train", "validation", "test"))
    assert total == len(read_rows(SAMPLE_PATH))


def test_split_is_deterministic_with_same_seed(tmp_path: Path) -> None:
    output_dir_a = tmp_path / "splits_a"
    output_dir_b = tmp_path / "splits_b"
    split_cli.main([str(SAMPLE_PATH), "--output-dir", str(output_dir_a), "--seed", "42"])
    split_cli.main([str(SAMPLE_PATH), "--output-dir", str(output_dir_b), "--seed", "42"])
    assert (output_dir_a / "train.jsonl").read_text(encoding="utf-8") == (output_dir_b / "train.jsonl").read_text(encoding="utf-8")
    assert (output_dir_a / "validation.jsonl").read_text(encoding="utf-8") == (output_dir_b / "validation.jsonl").read_text(encoding="utf-8")
    assert (output_dir_a / "test.jsonl").read_text(encoding="utf-8") == (output_dir_b / "test.jsonl").read_text(encoding="utf-8")


def test_generated_dry_run_rows_can_pass_audit(tmp_path: Path) -> None:
    rows = generate_synthetic_demo_rows(25)
    path = write_jsonl(tmp_path / "generated.jsonl", rows)
    summary = audit_cli.audit_jsonl_file(path, min_rows=25)
    assert summary.status == "PASS"
