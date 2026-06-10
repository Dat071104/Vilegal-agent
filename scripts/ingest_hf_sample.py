#!/usr/bin/env python3
"""
ingest_hf_sample.py — Phase 2A sample-only ingestion CLI.

Loads a small sample from a registered Vietnamese legal dataset source,
normalizes records, runs quality checks, and writes output files to
artifacts/<output-dir>/.

CRITICAL RULES (enforced in code):
  - --max-records default is 50; hard cap is 100.
  - --offline-fixture bypasses all network access.
  - Bulk download is BLOCKED.
  - Outputs are written to artifacts/ (gitignored).
  - No model training, RAG indexing, or QA generation.

Usage:
    python scripts/ingest_hf_sample.py --source uts_vlc --max-records 10 \\
        --offline-fixture tests/fixtures/synthetic_legal_articles.jsonl \\
        --output-dir artifacts/phase_2a_test

    python scripts/ingest_hf_sample.py --source uts_vlc --max-records 50

Output files (all in --output-dir):
    sample_normalized.jsonl   — Normalized records.
    rejected_records.jsonl    — Records that failed normalization.
    provenance_manifest.json  — Source provenance metadata.
    quality_report.json       — Quality metrics for this run.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Suppress Windows symlink warning from huggingface_hub (cosmetic only, not a security risk)
import os
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# Ensure src/ is on the path when run from the repo root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.ingestion.hf_sample_loader import load_records
from vilegal.ingestion.normalizers import normalize_record
from vilegal.ingestion.provenance import build_manifest, write_manifest
from vilegal.ingestion.quality_checks import run_quality_checks, write_quality_report
from vilegal.ingestion.source_registry import (
    DEFAULT_MAX_RECORDS,
    MAX_RECORDS_HARD_CAP,
    enforce_max_records,
    get_source,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_jsonl(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _print_summary(
    source_id: str,
    mode: str,
    total_seen: int,
    total_normalized: int,
    total_rejected: int,
    output_dir: Path,
    gate_passed: bool,
    violations: list[str],
) -> None:
    sep = "=" * 62
    print(f"\n{sep}")
    print("  ViLegal Agent — Phase 2A Sample Ingestion")
    print(f"{sep}")
    print(f"  Source         : {source_id}")
    print(f"  Load mode      : {mode}")
    print(f"  Records seen   : {total_seen}")
    print(f"  Normalized     : {total_normalized}")
    print(f"  Rejected       : {total_rejected}")
    print(f"  Output dir     : {output_dir}")
    print(f"  Quality gate   : {'PASS' if gate_passed else 'FAIL'}")
    if violations:
        print("  Violations     :")
        for v in violations:
            print(f"    - {v}")
    print(f"  Bulk download  : BLOCKED")
    print(f"{sep}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 2A sample-only ingestion. Bulk download is BLOCKED.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Registered source ID (e.g. 'uts_vlc', 'viet_legal_instruct', 'synthetic_example').",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=DEFAULT_MAX_RECORDS,
        help=f"Maximum records to load (default: {DEFAULT_MAX_RECORDS}, hard cap: {MAX_RECORDS_HARD_CAP}).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/phase_2a_sample_ingestion"),
        help="Directory for output files (default: artifacts/phase_2a_sample_ingestion).",
    )
    parser.add_argument(
        "--offline-fixture",
        type=Path,
        default=None,
        help="Path to a local JSONL file. Disables all network access.",
    )
    parser.add_argument(
        "--hf-split",
        default=None,
        help=(
            "HF dataset split to use when streaming. "
            "Defaults to the source's registered default_split "
            "(e.g. '2026' for UTS_VLC, 'train' for others)."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # --- Validate & clamp max_records ---
    try:
        max_records = enforce_max_records(args.max_records, args.source)
    except ValueError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        return 1

    # --- Resolve source ---
    try:
        source_meta = get_source(args.source)
    except KeyError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        return 1

    if not source_meta.approved_for_sample:
        print(
            f"\nError: Source '{args.source}' is NOT approved for sample ingestion. "
            f"Reason: {source_meta.notes}",
            file=sys.stderr,
        )
        return 1

    output_dir: Path = args.output_dir
    offline_fixture: Path | None = args.offline_fixture

    # Resolve HF split: explicit CLI flag > source registry default > 'train'
    hf_split: str = args.hf_split or source_meta.default_split

    # --- Load records ---
    retrieved_at = datetime.now(tz=timezone.utc).isoformat()
    try:
        raw_records, load_mode = load_records(
            hf_handle=source_meta.hf_handle,
            max_records=max_records,
            offline_fixture=offline_fixture,
            hf_split=hf_split,
        )
    except (FileNotFoundError, ValueError, RuntimeError, ImportError) as exc:
        print(f"\nError loading records: {exc}", file=sys.stderr)
        return 1

    # --- Normalize ---
    normalized: list[dict] = []
    rejected: list[dict] = []

    for raw in raw_records:
        try:
            record = normalize_record(
                raw=raw,
                source_dataset=source_meta.name,
                source_url=source_meta.url,
                license_str=source_meta.license,
                retrieved_at=retrieved_at,
            )
            normalized.append(record)
        except ValueError as exc:
            rejected.append({"error": str(exc), "raw": raw})

    # --- Write outputs ---
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(normalized, output_dir / "sample_normalized.jsonl")
    _write_jsonl(rejected, output_dir / "rejected_records.jsonl")

    # --- Provenance manifest ---
    manifest = build_manifest(
        source=source_meta,
        max_records=max_records,
        actual_records_seen=len(raw_records),
        offline_fixture=offline_fixture,
    )
    write_manifest(manifest, output_dir)

    # --- Quality report ---
    report = run_quality_checks(
        normalized_records=normalized,
        rejected_records=rejected,
        source_dataset=source_meta.name,
        max_records=max_records,
    )
    write_quality_report(report, output_dir)

    # --- Summary ---
    _print_summary(
        source_id=args.source,
        mode=load_mode,
        total_seen=report.total_seen,
        total_normalized=report.total_normalized,
        total_rejected=report.total_rejected,
        output_dir=output_dir,
        gate_passed=report.quality_gate_passed,
        violations=report.threshold_violations,
    )

    return 0 if report.quality_gate_passed else 2


if __name__ == "__main__":
    sys.exit(main())
