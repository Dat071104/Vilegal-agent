#!/usr/bin/env python3
"""
Phase 2H CLI for building a deterministic manual-review pack from Phase 2G outputs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.ingestion.review_sampler import (  # noqa: E402
    DEFAULT_SAMPLE_SIZE,
    DEFAULT_SEED,
    build_review_pack,
)


def resolve_artifacts_root() -> Path:
    return (ROOT / "artifacts").resolve()


def ensure_path_within_artifacts(path: Path) -> Path:
    resolved = path.resolve()
    artifacts_root = resolve_artifacts_root()
    if resolved != artifacts_root and artifacts_root not in resolved.parents:
        raise ValueError(f"Path must stay under artifacts/: {resolved}")
    return resolved


def ensure_safe_paths(input_dir: Path, output_dir: Path) -> tuple[Path, Path]:
    input_resolved = ensure_path_within_artifacts(input_dir)
    output_resolved = ensure_path_within_artifacts(output_dir)
    if not input_resolved.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_resolved}")
    if output_resolved == input_resolved or input_resolved in output_resolved.parents:
        raise ValueError("Output directory must not equal or nest inside the input directory.")
    return input_resolved, output_resolved


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a deterministic Phase 2H manual-review sampling pack.")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        input_dir, output_dir = ensure_safe_paths(args.input_dir, args.output_dir)
        result = build_review_pack(
            input_dir=input_dir,
            output_dir=output_dir,
            sample_size=args.sample_size,
            seed=args.seed,
            rubric_path=ROOT / "docs" / "MANUAL_REVIEW_RUBRIC.md",
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    report_path = output_dir / "sampling_report.json"
    print(f"Wrote Phase 2H review pack to {output_dir}")
    print(f"Sampling verdict: {result['sampling_report']['safety_verdict']}")
    print(f"Sampling report: {report_path}")
    return 0 if result["sampling_report"]["safety_verdict"] != "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
