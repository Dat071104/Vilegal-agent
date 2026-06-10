#!/usr/bin/env python3
"""
Create deterministic train/validation/test splits for Track A synthetic-demo data.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.demo_synthetic.generator import load_track_a_config  # noqa: E402
from vilegal.demo_synthetic.validator import load_jsonl_rows, validate_jsonl_file  # noqa: E402


def _resolve_output_dir(path: Path | None, default_output_dir: str) -> Path:
    candidate = path or Path(default_output_dir)
    return candidate if candidate.is_absolute() else ROOT / candidate


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def split_rows(
    rows: list[dict[str, object]],
    *,
    seed: int,
    train_ratio: float,
    validation_ratio: float,
    test_ratio: float,
) -> dict[str, list[dict[str, object]]]:
    total_ratio = train_ratio + validation_ratio + test_ratio
    if abs(total_ratio - 1.0) > 1e-9:
        raise ValueError("Split ratios must sum to 1.0.")

    shuffled = list(rows)
    random.Random(seed).shuffle(shuffled)

    total = len(shuffled)
    train_end = int(total * train_ratio)
    validation_end = train_end + int(total * validation_ratio)

    return {
        "train": shuffled[:train_end],
        "validation": shuffled[train_end:validation_end],
        "test": shuffled[validation_end:],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    config = load_track_a_config(ROOT / "configs" / "track_a_synthetic_demo.yaml")
    parser = argparse.ArgumentParser(description="Split Track A synthetic-demo JSONL into train/validation/test.")
    parser.add_argument("input_path", type=Path, help="Validated JSONL input path.")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=int(config.split["seed"]))
    parser.add_argument("--train-ratio", type=float, default=float(config.split["train_ratio"]))
    parser.add_argument("--validation-ratio", type=float, default=float(config.split["validation_ratio"]))
    parser.add_argument("--test-ratio", type=float, default=float(config.split["test_ratio"]))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = load_track_a_config(ROOT / "configs" / "track_a_synthetic_demo.yaml")
        summary = validate_jsonl_file(args.input_path)
        if summary.invalid_rows:
            raise ValueError(f"Input dataset is not valid synthetic-demo JSONL: {summary.invalid_rows} invalid rows.")
        rows = load_jsonl_rows(args.input_path)
        output_dir = _resolve_output_dir(args.output_dir, str(config.split["default_output_dir"]))
        splits = split_rows(
            rows,
            seed=args.seed,
            train_ratio=args.train_ratio,
            validation_ratio=args.validation_ratio,
            test_ratio=args.test_ratio,
        )
        for split_name, split_rows_payload in splits.items():
            _write_jsonl(output_dir / f"{split_name}.jsonl", split_rows_payload)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Track A synthetic split FAILED: {exc}", file=sys.stderr)
        return 1

    print("Track A synthetic split PASS")
    print(f"Train rows: {len(splits['train'])}")
    print(f"Validation rows: {len(splits['validation'])}")
    print(f"Test rows: {len(splits['test'])}")
    print(f"Output dir: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
