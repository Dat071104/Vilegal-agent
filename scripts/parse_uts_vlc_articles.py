#!/usr/bin/env python3
"""
Phase 2F secondary parser for existing UTS_VLC Phase 2D artifacts.

Reads normalized document-level records only from a local artifacts directory and
derives article/chunk candidates for analysis. This is not RAG indexing and not
legal verification.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.ingestion.article_parser import (  # noqa: E402
    build_metrics,
    build_parse_report,
    load_jsonl,
    parse_records,
    serialize_rejected,
    serialize_warning,
    validate_parent_provenance,
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


def ensure_safe_output_paths(input_dir: Path, output_dir: Path, report_out: Path | None) -> tuple[Path, Path, Path | None]:
    input_resolved = input_dir.resolve()
    output_resolved = ensure_path_within_artifacts(output_dir)
    if output_resolved == input_resolved or input_resolved in output_resolved.parents:
        raise ValueError("Output directory must not equal or nest inside the input directory.")
    if output_resolved.name == "uts_vlc" and "phase_2d_controlled_ingestion" in str(output_resolved):
        raise ValueError("Output directory must not target the Phase 2D artifact path.")

    report_resolved = None
    if report_out is not None:
        report_resolved = ensure_path_within_artifacts(report_out)
        if report_resolved == input_resolved:
            raise ValueError("Report path must not overwrite the input directory.")
        if report_resolved.parent == input_resolved:
            raise ValueError("Report path must not write inside the input directory.")
    return input_resolved, output_resolved, report_resolved


def required_input_files(input_dir: Path) -> list[Path]:
    return [
        input_dir / "sample_normalized.jsonl",
        input_dir / "provenance_manifest.json",
        input_dir / "quality_report.json",
    ]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse existing UTS_VLC document-level artifacts into article/chunk candidates."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Existing Phase 2D UTS_VLC artifacts directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Output directory under artifacts/ for Phase 2F parser outputs.",
    )
    parser.add_argument(
        "--report-out",
        type=Path,
        default=None,
        help="Optional explicit path under artifacts/ for a copy of parse_report.json.",
    )
    return parser.parse_args(argv)


def write_report(report_path: Path, report: dict[str, object]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        input_dir, output_dir, report_out = ensure_safe_output_paths(
            args.input_dir, args.output_dir, args.report_out
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    missing_inputs = [str(path) for path in required_input_files(input_dir) if not path.exists()]
    if missing_inputs:
        print(f"BLOCKED: missing required input files: {missing_inputs}", file=sys.stderr)
        return 2

    records = load_jsonl(input_dir / "sample_normalized.jsonl")
    blocked_missing_fields: list[str] = []
    for record in records:
        blocked_missing_fields.extend(validate_parent_provenance(record))

    if blocked_missing_fields:
        metrics = build_metrics(
            input_document_count=len(records),
            marker_counts=[0 for _ in records],
            candidates=[],
            warnings=[],
            provenance_failures=len(records),
        )
        report = build_parse_report(
            input_dir=input_dir,
            output_dir=output_dir,
            status="BLOCKED",
            blocked=True,
            reason="Missing required parent provenance fields.",
            metrics=metrics,
            warnings=[],
            blocked_missing_fields=blocked_missing_fields,
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        write_report(output_dir / "parse_report.json", as_report_dict(report))
        if report_out is not None:
            write_report(report_out, as_report_dict(report))
        print("BLOCKED: missing required parent provenance fields.", file=sys.stderr)
        return 2

    candidates, rejected, warnings, metrics = parse_records(records)
    empty_rate = 0.0 if metrics.derived_article_count == 0 else round(
        metrics.empty_derived_article_count / metrics.derived_article_count, 6
    )
    has_risks = any(
        [
            metrics.documents_without_article_markers > 0,
            metrics.duplicate_article_hash_count > 0,
            metrics.near_empty_derived_article_count > 0,
            metrics.suspicious_article_length_count > 0,
            metrics.parse_warning_count > 0,
        ]
    )
    status = (
        "PASS"
        if empty_rate <= 0.005 and metrics.parent_provenance_coverage == 1.0 and not has_risks
        else "PASS WITH RISKS"
    )
    reason = "Derived parser candidates created for analysis only."
    report = build_parse_report(
        input_dir=input_dir,
        output_dir=output_dir,
        status=status,
        blocked=False,
        reason=reason,
        metrics=metrics,
        warnings=warnings,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "article_candidates.jsonl", candidates)
    write_jsonl(output_dir / "rejected_documents.jsonl", [serialize_rejected(item) for item in rejected])
    write_jsonl(output_dir / "parse_warnings.jsonl", [serialize_warning(item) for item in warnings])
    write_report(output_dir / "parse_report.json", as_report_dict(report))
    if report_out is not None:
        write_report(report_out, as_report_dict(report))

    print(f"Wrote parser outputs to {output_dir}")
    if report_out is not None:
        print(f"Wrote report copy to {report_out}")
    return 0


def as_report_dict(report) -> dict[str, object]:
    return {
        "phase": report.phase,
        "parser_version": report.parser_version,
        "input_dir": report.input_dir,
        "output_dir": report.output_dir,
        "status": report.status,
        "blocked": report.blocked,
        "reason": report.reason,
        "metrics": report.metrics.__dict__,
        "safety_gates": report.safety_gates,
        "warnings_summary": report.warnings_summary,
        "blocked_missing_provenance_fields": report.blocked_missing_provenance_fields,
    }


if __name__ == "__main__":
    raise SystemExit(main())
