#!/usr/bin/env python3
"""
Inspect a local JSONL sample file without making network requests.

The script supports either:
    python scripts/inspect_data_source_sample.py
    python scripts/inspect_data_source_sample.py tests/fixtures/synthetic_legal_articles.jsonl
    python scripts/inspect_data_source_sample.py --file tests/fixtures/synthetic_legal_articles.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.data_contracts import LegalArticle  # noqa: E402


DEFAULT_SAMPLE_FILE = ROOT / "tests" / "fixtures" / "synthetic_legal_articles.jsonl"


def load_jsonl(filepath: Path, limit: int) -> list[dict]:
    """Load up to ``limit`` non-empty JSONL records."""

    records: list[dict] = []
    with filepath.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if index >= limit:
                break
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def validate_records(records: list[dict]) -> tuple[list[LegalArticle], list[str], bool]:
    """Validate records as article-level examples and confirm they are synthetic."""

    validated: list[LegalArticle] = []
    errors: list[str] = []
    synthetic_only = True

    for index, record in enumerate(records, start=1):
        try:
            article = LegalArticle.model_validate(record)
        except Exception as exc:  # pragma: no cover - exercised via CLI path
            errors.append(f"Record {index}: {exc}")
            synthetic_only = False
            continue

        validated.append(article)
        if not article.is_synthetic_example or article.source_dataset != "synthetic_example":
            synthetic_only = False

    return validated, errors, synthetic_only


def print_summary(records: list[LegalArticle], filepath: Path, synthetic_only: bool) -> None:
    """Print a compact summary for human review."""

    print(f"\n{'=' * 60}")
    print("  ViLegal Agent - Data Source Inspector")
    print(f"{'=' * 60}")
    print(f"  File           : {filepath}")
    print(f"  Count          : {len(records)} validated record(s)")
    print(f"  Synthetic only : {synthetic_only}")
    print(f"{'=' * 60}\n")

    for index, article in enumerate(records, start=1):
        preview = article.text[:77] + "..." if len(article.text) > 80 else article.text
        print(f"  Record #{index}")
        print(f"    doc_id          : {article.doc_id}")
        print(f"    doc_type        : {article.doc_type}")
        print(f"    number          : {article.number}")
        print(f"    article_number  : {article.article_number}")
        print(f"    source_dataset  : {article.source_dataset}")
        print(f"    source_id       : {article.source_id}")
        print(f"    is_synthetic    : {article.is_synthetic_example}")
        print(f"    text            : {preview}")
        print()

    print(f"{'=' * 60}")
    print("  Inspection complete. No network calls were made.")
    print(f"{'=' * 60}\n")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Inspect a local JSONL data sample.")
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        default=None,
        help=f"Path to the JSONL file to inspect (default: {DEFAULT_SAMPLE_FILE}).",
    )
    parser.add_argument(
        "--file",
        dest="file_flag",
        type=Path,
        default=None,
        help="Alias for the input file path.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of records to display (default: 10).",
    )
    return parser.parse_args()


def resolve_filepath(args: argparse.Namespace) -> Path:
    """Resolve the file path from positional or flag input."""

    if args.file is not None and args.file_flag is not None:
        raise ValueError("Use either the positional file path or --file, not both.")
    return args.file or args.file_flag or DEFAULT_SAMPLE_FILE


def main() -> int:
    """CLI entry point."""

    args = parse_args()

    try:
        filepath = resolve_filepath(args)
    except ValueError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        return 1

    if not filepath.exists():
        print(f"\nError: file not found: {filepath}", file=sys.stderr)
        return 1

    if filepath.suffix != ".jsonl":
        print(f"\nWarning: file extension is not .jsonl: {filepath}", file=sys.stderr)

    try:
        raw_records = load_jsonl(filepath, limit=args.limit)
    except json.JSONDecodeError as exc:
        print(f"\nError: failed to parse JSONL: {exc}", file=sys.stderr)
        return 1

    if not raw_records:
        print(f"\nWarning: no records found in {filepath}")
        return 0

    validated_records, errors, synthetic_only = validate_records(raw_records)
    if errors:
        print("\nSchema validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if filepath.resolve() == DEFAULT_SAMPLE_FILE.resolve() and not synthetic_only:
        print(
            "\nError: the default sample file contains non-synthetic records.",
            file=sys.stderr,
        )
        return 1

    print_summary(validated_records, filepath, synthetic_only)
    return 0


if __name__ == "__main__":
    sys.exit(main())
