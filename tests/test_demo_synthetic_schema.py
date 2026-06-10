from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from vilegal.demo_synthetic.generator import generate_synthetic_demo_rows
from vilegal.demo_synthetic.validator import validate_jsonl_file


ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = ROOT / "data" / "synthetic_demo" / "sample_qa.jsonl"
GENERATE_SCRIPT = ROOT / "scripts" / "generate_synthetic_demo_qa.py"


def read_sample_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with SAMPLE_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_sample_qa_file_exists() -> None:
    assert SAMPLE_PATH.is_file()


def test_all_sample_rows_are_valid_json() -> None:
    rows = read_sample_rows()
    assert rows
    assert all(isinstance(row, dict) for row in rows)


def test_all_sample_rows_have_synthetic_source() -> None:
    rows = read_sample_rows()
    assert all(row["source"] == "synthetic-demo" for row in rows)


def test_all_sample_rows_have_synthetic_flags_locked_down() -> None:
    rows = read_sample_rows()
    assert all(row["is_synthetic"] is True for row in rows)
    assert all(row["is_legal_ground_truth"] is False for row in rows)
    assert all(row["approved_for_rag_index"] is False for row in rows)


def test_generator_dry_run_can_create_temporary_valid_jsonl_file(tmp_path: Path) -> None:
    output_path = tmp_path / "dry_run.jsonl"
    result = subprocess.run(
        [
            sys.executable,
            str(GENERATE_SCRIPT),
            "--dry-run",
            "--count",
            "5",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    summary = validate_jsonl_file(output_path)
    assert summary.invalid_rows == 0
    assert summary.valid_rows == 5


def test_generator_dry_run_does_not_require_internet_or_api_keys(tmp_path: Path, monkeypatch) -> None:
    output_path = tmp_path / "dry_run.jsonl"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = subprocess.run(
        [
            sys.executable,
            str(GENERATE_SCRIPT),
            "--dry-run",
            "--count",
            "3",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Provider: template" in result.stdout


def test_generator_library_returns_expected_count() -> None:
    rows = generate_synthetic_demo_rows(4)
    assert len(rows) == 4
    assert rows[0].id == "synthetic-demo-000001"
