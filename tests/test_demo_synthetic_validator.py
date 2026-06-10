from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from vilegal.demo_synthetic.validator import validate_jsonl_file


ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = ROOT / "data" / "synthetic_demo" / "sample_qa.jsonl"
VALIDATE_SCRIPT = ROOT / "scripts" / "validate_synthetic_demo_qa.py"


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


def test_validator_passes_on_sample_file() -> None:
    summary = validate_jsonl_file(SAMPLE_PATH)
    assert summary.total_rows >= 10
    assert summary.invalid_rows == 0


def test_validator_cli_passes_on_sample_file() -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), str(SAMPLE_PATH)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Invalid rows: 0" in result.stdout


def test_validator_fails_on_missing_disclaimer(tmp_path: Path) -> None:
    rows = read_rows(SAMPLE_PATH)
    rows[0]["disclaimer"] = ""
    path = write_rows(tmp_path / "missing_disclaimer.jsonl", rows)
    summary = validate_jsonl_file(path)
    assert summary.invalid_rows == 1


def test_validator_fails_on_non_synthetic_source(tmp_path: Path) -> None:
    rows = read_rows(SAMPLE_PATH)
    rows[0]["source"] = "uts-vlc"
    path = write_rows(tmp_path / "bad_source.jsonl", rows)
    summary = validate_jsonl_file(path)
    assert summary.invalid_rows == 1


def test_validator_fails_on_approved_for_rag_index_true(tmp_path: Path) -> None:
    rows = read_rows(SAMPLE_PATH)
    rows[0]["approved_for_rag_index"] = True
    path = write_rows(tmp_path / "bad_rag.jsonl", rows)
    summary = validate_jsonl_file(path)
    assert summary.invalid_rows == 1
