#!/usr/bin/env python3
"""
Validate Track A synthetic-demo QA rows without internet or API keys.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.demo_synthetic.validator import validate_jsonl_file  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Track A synthetic-demo QA JSONL.")
    parser.add_argument("input_path", type=Path, help="Path to the JSONL file to validate.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = validate_jsonl_file(args.input_path)
    except FileNotFoundError as exc:
        print(f"Track A synthetic validation FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"Total rows: {summary.total_rows}")
    print(f"Valid rows: {summary.valid_rows}")
    print(f"Invalid rows: {summary.invalid_rows}")

    for issue in summary.issues[:10]:
        print(f"Line {issue.line_number}: {'; '.join(issue.errors)}", file=sys.stderr)

    if summary.invalid_rows:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
