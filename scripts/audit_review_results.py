#!/usr/bin/env python3
"""
Phase 2J CLI for auditing completed human review results.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.ingestion.review_audit import (  # noqa: E402
    BLOCKED_STATUS,
    audit_review_results,
)


def resolve_artifacts_root() -> Path:
    return (ROOT / "artifacts").resolve()


def ensure_path_within_artifacts(path: Path) -> Path:
    resolved = path.resolve()
    artifacts_root = resolve_artifacts_root()
    if resolved != artifacts_root and artifacts_root not in resolved.parents:
        raise ValueError(f"Path must stay under artifacts/: {resolved}")
    return resolved


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Phase 2J completed human review results.")
    parser.add_argument("--review-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        output_dir = ensure_path_within_artifacts(args.output_dir)
        report, _ = audit_review_results(args.review_file, output_dir)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Review file: {args.review_file}")
    print(f"Output dir: {output_dir}")
    print(f"Status: {report.status}")
    print(f"Reason: {report.reason}")
    print(f"Metrics: {report.metrics}")
    if report.status == "FAIL":
        return 2
    if report.status == BLOCKED_STATUS:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
