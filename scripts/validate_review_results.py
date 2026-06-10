#!/usr/bin/env python3
"""
Phase 2I CLI for validating human review results from the Phase 2H template.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.ingestion.review_results import (  # noqa: E402
    report_to_dict,
    validate_review_results_file,
    write_json,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Phase 2I human review results CSV.")
    parser.add_argument("--review-file", type=Path, required=True)
    parser.add_argument("--report-out", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        _, report = validate_review_results_file(args.review_file)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    payload = report_to_dict(report)
    if args.report_out is not None:
        write_json(args.report_out, payload)

    print(f"Review file: {args.review_file}")
    print(f"Rows: total={report.total_rows} valid={report.valid_rows} invalid={report.invalid_rows}")
    print(f"Decision counts: {report.decision_counts}")
    print(f"Adjudication counts: {report.adjudication_counts}")
    print(f"Safety verdict: {report.safety_verdict}")
    if args.report_out is not None:
        print(f"Report written to: {args.report_out}")
    return 0 if report.safety_verdict != "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
