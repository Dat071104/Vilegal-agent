#!/usr/bin/env python3
"""
Generate synthetic-demo QA rows for Track A without touching Track B corpus data.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.demo_synthetic.generator import generate_synthetic_demo_rows, load_track_a_config, write_jsonl  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Track A synthetic-demo QA rows.")
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "track_a_synthetic_demo.yaml")
    parser.add_argument("--count", type=int, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--provider", choices=("template", "openai"), default="template")
    parser.add_argument("--dry-run", action="store_true", help="Force offline template generation.")
    parser.add_argument("--live", action="store_true", help="Disable default dry-run behavior.")
    return parser.parse_args(argv)


def resolve_output_path(path: Path | None, default_output: str) -> Path:
    candidate = path or Path(default_output)
    return candidate if candidate.is_absolute() else ROOT / candidate


def ensure_live_output_policy(path: Path) -> None:
    artifacts_root = (ROOT / "artifacts").resolve()
    resolved = path.resolve()
    if resolved != artifacts_root and artifacts_root not in resolved.parents:
        raise ValueError("Live generation outputs must stay under artifacts/.")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        config = load_track_a_config(args.config)
        count = args.count or int(config.generation["target_total_pairs"])
        dry_run = args.dry_run or (bool(config.generation["default_dry_run"]) and not args.live)
        output_path = resolve_output_path(args.output, str(config.generation["default_output_path"]))

        if args.provider == "openai" and not dry_run:
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY is required for future live API generation.")
            raise NotImplementedError("OpenAI provider hook is reserved for a future Track A phase.")

        if not dry_run:
            ensure_live_output_policy(output_path)

        rows = generate_synthetic_demo_rows(count, disclaimer=str(config.metadata["disclaimer"]))
        write_jsonl(output_path, rows)
    except (FileNotFoundError, NotImplementedError, ValueError) as exc:
        print(f"Track A synthetic generation FAILED: {exc}", file=sys.stderr)
        return 1

    print("Track A synthetic generation PASS")
    print(f"Rows written: {count}")
    print(f"Dry run: {dry_run}")
    print(f"Provider: {args.provider}")
    print(f"Output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
