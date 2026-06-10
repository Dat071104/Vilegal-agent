#!/usr/bin/env python3
"""
Phase 2K CLI for building a reviewed sample-scope corpus candidate manifest.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.ingestion.corpus_manifest import build_corpus_candidate_manifest  # noqa: E402


def resolve_artifacts_root() -> Path:
    return (ROOT / "artifacts").resolve()


def ensure_path_within_artifacts(path: Path) -> Path:
    resolved = path.resolve()
    artifacts_root = resolve_artifacts_root()
    if resolved != artifacts_root and artifacts_root not in resolved.parents:
        raise ValueError(f"Path must stay under artifacts/: {resolved}")
    return resolved


def ensure_safe_dirs(review_audit_dir: Path, review_pack_dir: Path, filter_dir: Path, output_dir: Path) -> tuple[Path, Path, Path, Path]:
    audit_resolved = ensure_path_within_artifacts(review_audit_dir)
    pack_resolved = ensure_path_within_artifacts(review_pack_dir)
    filter_resolved = ensure_path_within_artifacts(filter_dir)
    output_resolved = ensure_path_within_artifacts(output_dir)
    return audit_resolved, pack_resolved, filter_resolved, output_resolved


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a deterministic Phase 2K corpus candidate manifest.")
    parser.add_argument("--review-audit-dir", type=Path, required=True)
    parser.add_argument("--review-pack-dir", type=Path, required=True)
    parser.add_argument("--filter-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        review_audit_dir, review_pack_dir, filter_dir, output_dir = ensure_safe_dirs(
            args.review_audit_dir,
            args.review_pack_dir,
            args.filter_dir,
            args.output_dir,
        )
        report, _ = build_corpus_candidate_manifest(
            review_audit_dir=review_audit_dir,
            review_pack_dir=review_pack_dir,
            filter_dir=filter_dir,
            output_dir=output_dir,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Output dir: {output_dir}")
    print(f"Manifest verdict: {report.status}")
    print(f"Accepted input rows: {report.metrics.accepted_candidate_ids_input_count}")
    print(f"Manifest records written: {report.metrics.manifest_records_written}")
    print(f"Missing review metadata count: {report.metrics.missing_review_metadata_count}")
    print(f"Missing filter metadata count: {report.metrics.missing_filter_metadata_count}")
    return 0 if report.status != "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
