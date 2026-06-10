#!/usr/bin/env python3
"""
Phase 2G filtering CLI for parser-derived UTS article/chunk candidates.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.ingestion.article_filter import (  # noqa: E402
    FilterMetrics,
    as_report_dict,
    build_report,
    classify_candidates,
    compute_metrics,
    load_jsonl,
    write_json,
    write_jsonl,
)


def resolve_artifacts_root() -> Path:
    return (ROOT / "artifacts").resolve()


def ensure_path_within_artifacts(path: Path) -> Path:
    resolved = path.resolve()
    artifacts_root = resolve_artifacts_root()
    if resolved != artifacts_root and artifacts_root not in resolved.parents:
        raise ValueError(f"Path must stay under artifacts/: {resolved}")
    return resolved


def ensure_safe_paths(input_dir: Path, output_dir: Path, report_out: Path | None) -> tuple[Path, Path, Path | None]:
    input_resolved = input_dir.resolve()
    output_resolved = ensure_path_within_artifacts(output_dir)
    if not input_resolved.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_resolved}")
    if output_resolved == input_resolved or input_resolved in output_resolved.parents:
        raise ValueError("Output directory must not equal or nest inside the input directory.")

    report_resolved = None
    if report_out is not None:
        report_resolved = ensure_path_within_artifacts(report_out)
        if report_resolved.parent == input_resolved:
            raise ValueError("Report path must not write inside the input directory.")
    return input_resolved, output_resolved, report_resolved


def required_input_files(input_dir: Path) -> list[Path]:
    return [
        input_dir / "article_candidates.jsonl",
        input_dir / "parse_report.json",
        input_dir / "parse_warnings.jsonl",
    ]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply deterministic review buckets to UTS article candidates.")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report-out", type=Path, default=None)
    return parser.parse_args(argv)


def resolve_source_manifest(input_dir: Path) -> Path:
    parse_report = json.loads((input_dir / "parse_report.json").read_text(encoding="utf-8"))
    source_manifest = Path(parse_report["input_dir"]) / "provenance_manifest.json"
    return source_manifest.resolve()


def blocked_metrics(total_input_candidates: int = 0) -> FilterMetrics:
    return FilterMetrics(
        total_input_candidates=total_input_candidates,
        total_output_records=0,
        total_rejected=0,
        total_needs_review=0,
        total_keep_candidate_for_human_review=0,
        rejected_by_reason={},
        needs_review_by_reason={},
        duplicate_hash_groups=0,
        duplicate_candidates_rejected=0,
        parent_document_warning_count=0,
        missing_required_fields_count=0,
        empty_count=0,
        near_empty_count=0,
        suspicious_length_count=0,
        preamble_warning_count=0,
        marker_uncertainty_count=0,
        parent_provenance_coverage=0.0,
        approved_for_rag_index_true_count=0,
        is_legal_ground_truth_true_count=0,
        safety_verdict="FAIL",
    )


def write_blocked_report(
    *,
    input_dir: Path,
    output_dir: Path,
    report_out: Path | None,
    source_manifest_path: Path,
    reason: str,
    missing_fields: list[str],
    total_input_candidates: int = 0,
) -> None:
    report = build_report(
        input_dir=input_dir,
        output_dir=output_dir,
        source_manifest_path=source_manifest_path,
        reason=reason,
        metrics=blocked_metrics(total_input_candidates),
        blocked=True,
        missing_required_fields=missing_fields,
    )
    write_json(output_dir / "filter_report.json", as_report_dict(report))
    if report_out is not None:
        write_json(report_out, as_report_dict(report))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        input_dir, output_dir, report_out = ensure_safe_paths(args.input_dir, args.output_dir, args.report_out)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    missing_inputs = [str(path) for path in required_input_files(input_dir) if not path.exists()]
    if missing_inputs:
        print(f"Error: missing required input files: {missing_inputs}", file=sys.stderr)
        return 2

    source_manifest_path = resolve_source_manifest(input_dir)
    candidates = load_jsonl(input_dir / "article_candidates.jsonl")
    if not source_manifest_path.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        write_blocked_report(
            input_dir=input_dir,
            output_dir=output_dir,
            report_out=report_out,
            source_manifest_path=source_manifest_path,
            reason="Missing required source manifest.",
            missing_fields=["source_manifest"],
            total_input_candidates=len(candidates),
        )
        print("FAIL: missing required source manifest.", file=sys.stderr)
        return 2

    warnings = load_jsonl(input_dir / "parse_warnings.jsonl")
    all_records, rejected, needs_review, duplicate_group_sizes = classify_candidates(candidates, warnings)
    metrics = compute_metrics(
        candidates,
        all_records,
        rejected,
        needs_review,
        duplicate_group_sizes,
        len(warnings),
    )
    report = build_report(
        input_dir=input_dir,
        output_dir=output_dir,
        source_manifest_path=source_manifest_path,
        reason="Deterministic review labeling only. No candidate approved for RAG.",
        metrics=metrics,
        duplicate_group_sizes=duplicate_group_sizes,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "filtered_candidates.jsonl", all_records)
    write_jsonl(output_dir / "rejected_candidates.jsonl", rejected)
    write_jsonl(output_dir / "needs_review_candidates.jsonl", needs_review)
    write_json(output_dir / "decision_counts.json", {
        "total_input_candidates": metrics.total_input_candidates,
        "total_output_records": metrics.total_output_records,
        "total_rejected": metrics.total_rejected,
        "total_needs_review": metrics.total_needs_review,
        "total_keep_candidate_for_human_review": metrics.total_keep_candidate_for_human_review,
    })
    write_json(output_dir / "filter_report.json", as_report_dict(report))
    if report_out is not None:
        write_json(report_out, as_report_dict(report))

    print(f"Wrote filtered outputs to {output_dir}")
    if report_out is not None:
        print(f"Wrote report copy to {report_out}")
    return 0 if metrics.safety_verdict != "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
