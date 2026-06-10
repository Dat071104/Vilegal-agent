#!/usr/bin/env python3
"""
Audit Track A synthetic-demo QA rows for quality and safety.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.demo_synthetic.generator import load_track_a_config  # noqa: E402
from vilegal.demo_synthetic.validator import load_jsonl_rows, validate_demo_row  # noqa: E402


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _duplicate_count(counter: Counter[str]) -> int:
    return sum(count - 1 for count in counter.values() if count > 1)


@dataclass(frozen=True)
class AuditSummary:
    total_rows: int
    valid_rows: int
    invalid_rows: int
    minimum_rows_required: int
    duplicate_id_count: int
    duplicate_instruction_hash_count: int
    duplicate_input_hash_count: int
    duplicate_output_hash_count: int
    duplicate_triplet_hash_count: int
    task_type_distribution: dict[str, int]
    difficulty_distribution: dict[str, int]
    missing_or_invalid_field_count: int
    official_authority_claim_count: int
    source_mismatch_count: int
    synthetic_false_count: int
    legal_ground_truth_true_count: int
    approved_for_rag_index_true_count: int
    disclaimer_missing_count: int
    issue_frequencies: dict[str, int]
    status: str
    failures: list[str]


def audit_jsonl_file(path: str | Path, *, min_rows: int = 0) -> AuditSummary:
    rows = load_jsonl_rows(path)

    id_counter: Counter[str] = Counter()
    instruction_hash_counter: Counter[str] = Counter()
    input_hash_counter: Counter[str] = Counter()
    output_hash_counter: Counter[str] = Counter()
    triplet_hash_counter: Counter[str] = Counter()
    task_type_counter: Counter[str] = Counter()
    difficulty_counter: Counter[str] = Counter()
    issue_counter: Counter[str] = Counter()

    valid_rows = 0
    invalid_rows = 0
    missing_or_invalid_field_count = 0
    official_authority_claim_count = 0
    source_mismatch_count = 0
    synthetic_false_count = 0
    legal_ground_truth_true_count = 0
    approved_for_rag_index_true_count = 0
    disclaimer_missing_count = 0

    for row in rows:
        row_id = str(row.get("id", ""))
        id_counter[row_id] += 1

        instruction = str(row.get("instruction", ""))
        row_input = str(row.get("input", ""))
        output = str(row.get("output", ""))
        instruction_hash_counter[_hash_text(instruction)] += 1
        input_hash_counter[_hash_text(row_input)] += 1
        output_hash_counter[_hash_text(output)] += 1
        triplet_hash_counter[_hash_text("||".join((instruction, row_input, output)))] += 1

        task_type_counter[str(row.get("task_type", "missing"))] += 1
        difficulty_counter[str(row.get("difficulty", "missing"))] += 1

        errors = validate_demo_row(row)
        if errors:
            invalid_rows += 1
        else:
            valid_rows += 1

        for error in errors:
            issue_counter[error] += 1
            missing_or_invalid_field_count += 1
            if "official legal authority" in error:
                official_authority_claim_count += 1
            if "source must equal synthetic-demo" in error:
                source_mismatch_count += 1
            if "is_synthetic must be true" in error:
                synthetic_false_count += 1
            if "is_legal_ground_truth must be false" in error:
                legal_ground_truth_true_count += 1
            if "approved_for_rag_index must be false" in error:
                approved_for_rag_index_true_count += 1
            if "disclaimer" in error:
                disclaimer_missing_count += 1

    failures: list[str] = []
    if len(rows) < min_rows:
        failures.append(f"Row count below minimum: {len(rows)} < {min_rows}")
    duplicate_id_count = _duplicate_count(id_counter)
    if duplicate_id_count > 0:
        failures.append(f"Duplicate IDs found: {duplicate_id_count}")
    if approved_for_rag_index_true_count > 0:
        failures.append("approved_for_rag_index=true detected.")
    if legal_ground_truth_true_count > 0:
        failures.append("is_legal_ground_truth=true detected.")
    if source_mismatch_count > 0:
        failures.append("Non-synthetic source detected.")
    if disclaimer_missing_count > 0:
        failures.append("Missing or invalid disclaimer detected.")
    if official_authority_claim_count > 0:
        failures.append("Official legal authority claims detected.")
    if invalid_rows > 0:
        failures.append(f"Invalid rows detected: {invalid_rows}")

    status = "PASS" if not failures else "FAIL"
    return AuditSummary(
        total_rows=len(rows),
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        minimum_rows_required=min_rows,
        duplicate_id_count=duplicate_id_count,
        duplicate_instruction_hash_count=_duplicate_count(instruction_hash_counter),
        duplicate_input_hash_count=_duplicate_count(input_hash_counter),
        duplicate_output_hash_count=_duplicate_count(output_hash_counter),
        duplicate_triplet_hash_count=_duplicate_count(triplet_hash_counter),
        task_type_distribution=dict(task_type_counter),
        difficulty_distribution=dict(difficulty_counter),
        missing_or_invalid_field_count=missing_or_invalid_field_count,
        official_authority_claim_count=official_authority_claim_count,
        source_mismatch_count=source_mismatch_count,
        synthetic_false_count=synthetic_false_count,
        legal_ground_truth_true_count=legal_ground_truth_true_count,
        approved_for_rag_index_true_count=approved_for_rag_index_true_count,
        disclaimer_missing_count=disclaimer_missing_count,
        issue_frequencies=dict(issue_counter),
        status=status,
        failures=failures,
    )


def _write_json_report(path: Path, summary: AuditSummary) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(summary), ensure_ascii=False, indent=2), encoding="utf-8")


def _write_markdown_report(path: Path, summary: AuditSummary) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Track A Synthetic Audit Report",
        "",
        f"- Status: `{summary.status}`",
        f"- Total rows: `{summary.total_rows}`",
        f"- Valid rows: `{summary.valid_rows}`",
        f"- Invalid rows: `{summary.invalid_rows}`",
        f"- Duplicate IDs: `{summary.duplicate_id_count}`",
        f"- Duplicate instruction hashes: `{summary.duplicate_instruction_hash_count}`",
        f"- Duplicate input hashes: `{summary.duplicate_input_hash_count}`",
        f"- Duplicate output hashes: `{summary.duplicate_output_hash_count}`",
        f"- Duplicate triplet hashes: `{summary.duplicate_triplet_hash_count}`",
        f"- Task type distribution: `{summary.task_type_distribution}`",
        f"- Difficulty distribution: `{summary.difficulty_distribution}`",
        f"- Failures: `{summary.failures}`",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_report(path: Path, summary: AuditSummary) -> None:
    if path.suffix.lower() == ".md":
        _write_markdown_report(path, summary)
    else:
        _write_json_report(path, summary)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    config = load_track_a_config(ROOT / "configs" / "track_a_synthetic_demo.yaml")
    parser = argparse.ArgumentParser(description="Audit Track A synthetic-demo QA JSONL.")
    parser.add_argument("input_path", type=Path, help="Path to the JSONL file to audit.")
    parser.add_argument("--min-rows", type=int, default=int(config.audit["minimum_row_count"]))
    parser.add_argument("--report-out", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = audit_jsonl_file(args.input_path, min_rows=args.min_rows)
        if args.report_out is not None:
            write_report(args.report_out, summary)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Track A synthetic audit FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"Status: {summary.status}")
    print(f"Total rows: {summary.total_rows}")
    print(f"Valid rows: {summary.valid_rows}")
    print(f"Invalid rows: {summary.invalid_rows}")
    print(f"Duplicate IDs: {summary.duplicate_id_count}")
    print(f"Task types: {summary.task_type_distribution}")
    print(f"Difficulties: {summary.difficulty_distribution}")
    if summary.failures:
        for failure in summary.failures:
            print(failure, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
