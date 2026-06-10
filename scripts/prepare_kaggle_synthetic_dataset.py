#!/usr/bin/env python3
"""
Prepare a Kaggle-ready dataset package from Track A synthetic-demo splits.

Usage:
    python scripts/prepare_kaggle_synthetic_dataset.py \
        --split-dir artifacts/track_a_synthetic_demo/splits \
        --output-dir artifacts/track_a_kaggle_dataset \
        --zip-out artifacts/track_a_kaggle_dataset.zip

Rules:
- No internet required.
- No API keys required.
- Do not stage artifacts/.
- Output folder is for local manual upload to Kaggle only.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.demo_synthetic.validator import validate_jsonl_file  # noqa: E402

DATASET_CARD_CONTENT = """\
# ViLegal Synthetic Demo Dataset

## IMPORTANT DISCLAIMER

**SYNTHETIC DEMO ONLY — NOT LEGAL ADVICE — NOT OFFICIAL LEGAL TEXT**

This dataset is for AI engineering portfolio demonstration purposes only.

- All data is synthetically generated.
- No data represents real legal ground truth.
- No data is approved for RAG indexing.
- This dataset does NOT prove legal correctness.
- Do NOT use for actual legal compliance without consulting a qualified attorney.

## Source

- `source`: `synthetic-demo`
- `is_synthetic`: `true`
- `is_legal_ground_truth`: `false`
- `approved_for_rag_index`: `false`

## Splits

| Split      | Rows |
|------------|------|
| train      | 2000 |
| validation |  250 |
| test       |  250 |

## Schema

Each row is a JSONL object with Alpaca-style fields:
- `id`: unique identifier (starts with `synthetic-demo-`)
- `instruction`: task instruction string
- `input`: optional context (may be empty string)
- `output`: expected response
- `source`: always `synthetic-demo`
- `format`: always `alpaca`
- `domain`: always `vietnamese-legal-demo`
- `task_type`: one of `classification`, `explanation`, `retrieval_style_qa`, `drafting_demo`
- `difficulty`: one of `easy`, `medium`, `hard`
- `is_synthetic`: always `true`
- `is_legal_ground_truth`: always `false`
- `approved_for_rag_index`: always `false`
- `disclaimer`: synthetic-only disclaimer text

## Usage

This dataset is intended for Kaggle fine-tune demo experiments only.
Upload manually to Kaggle as a private dataset before running the
`track_a_kaggle_synthetic_finetune_demo.ipynb` notebook.

Track A demonstrates AI engineering mechanics, not real legal capability.
Track B real legal corpus governance remains blocked for QA/SFT/RAG.
"""

EXPECTED_COUNTS: dict[str, int] = {
    "train.jsonl": 2000,
    "validation.jsonl": 250,
    "test.jsonl": 250,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package Track A synthetic-demo splits into a Kaggle-ready dataset folder."
    )
    parser.add_argument(
        "--split-dir",
        type=Path,
        default=ROOT / "artifacts" / "track_a_synthetic_demo" / "splits",
        help="Directory containing train.jsonl, validation.jsonl, test.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "artifacts" / "track_a_kaggle_dataset",
        help="Output directory for the Kaggle-ready dataset package.",
    )
    parser.add_argument(
        "--zip-out",
        type=Path,
        default=None,
        help="Optional: path to write a zip archive of the output directory.",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip per-row synthetic validation (faster, not recommended).",
    )
    return parser.parse_args(argv)


def validate_split_file(
    split_path: Path,
    expected_rows: int,
    *,
    run_validator: bool = True,
) -> None:
    """Validate a single split file for safety constraints and expected row count."""
    if not split_path.exists():
        raise FileNotFoundError(f"Split file not found: {split_path}")

    # Count rows and check field-level constraints
    actual_rows = 0
    bad_rows: list[str] = []

    with split_path.open("r", encoding="utf-8") as fh:
        for line_no, raw_line in enumerate(fh, start=1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            actual_rows += 1
            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                bad_rows.append(f"Line {line_no}: invalid JSON — {exc.msg}")
                continue

            errs: list[str] = []
            if row.get("source") != "synthetic-demo":
                errs.append(f"source={row.get('source')!r} (expected 'synthetic-demo')")
            if row.get("is_synthetic") is not True:
                errs.append(f"is_synthetic={row.get('is_synthetic')!r} (expected true)")
            if row.get("is_legal_ground_truth") is not False:
                errs.append(
                    f"is_legal_ground_truth={row.get('is_legal_ground_truth')!r} (expected false)"
                )
            if row.get("approved_for_rag_index") is not False:
                errs.append(
                    f"approved_for_rag_index={row.get('approved_for_rag_index')!r} (expected false)"
                )
            if errs:
                bad_rows.append(f"Line {line_no}: " + "; ".join(errs))

    if bad_rows:
        print(f"  [FAIL] Field constraint violations in {split_path.name}:", file=sys.stderr)
        for msg in bad_rows[:20]:
            print(f"    {msg}", file=sys.stderr)
        raise SystemExit(1)

    if actual_rows != expected_rows:
        print(
            f"  [FAIL] {split_path.name}: expected {expected_rows} rows, got {actual_rows}.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    print(f"  [OK]   {split_path.name}: {actual_rows} rows, field constraints passed.")

    if run_validator:
        summary = validate_jsonl_file(split_path)
        if summary.invalid_rows:
            print(
                f"  [FAIL] {split_path.name}: {summary.invalid_rows} invalid rows detected by validator.",
                file=sys.stderr,
            )
            for issue in summary.issues[:10]:
                print(
                    f"    Line {issue.line_number}: {'; '.join(issue.errors)}", file=sys.stderr
                )
            raise SystemExit(1)
        print(
            f"  [OK]   {split_path.name}: validator passed ({summary.valid_rows}/{summary.total_rows} valid)."
        )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    split_dir: Path = args.split_dir
    output_dir: Path = args.output_dir
    zip_out: Path | None = args.zip_out
    run_validator = not args.skip_validation

    print("=" * 60)
    print("Track A2 — Kaggle Synthetic Dataset Packager")
    print("SYNTHETIC DEMO ONLY — NOT LEGAL ADVICE")
    print("=" * 60)

    # 1. Validate inputs
    print(f"\n[Step 1] Validating split files in: {split_dir}")
    for filename, expected_count in EXPECTED_COUNTS.items():
        split_path = split_dir / filename
        validate_split_file(split_path, expected_count, run_validator=run_validator)

    # 2. Create output directory
    print(f"\n[Step 2] Creating output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3. Copy split files
    print("\n[Step 3] Copying split files...")
    for filename in EXPECTED_COUNTS:
        src = split_dir / filename
        dst = output_dir / filename
        shutil.copy2(src, dst)
        print(f"  Copied: {filename}")

    # 4. Write dataset card
    card_path = output_dir / "DATASET_CARD.md"
    card_path.write_text(DATASET_CARD_CONTENT, encoding="utf-8")
    print(f"\n[Step 4] Dataset card written: {card_path}")

    # 5. Optional zip
    if zip_out is not None:
        print(f"\n[Step 5] Creating zip archive: {zip_out}")
        zip_out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for item in sorted(output_dir.iterdir()):
                zf.write(item, arcname=item.name)
                print(f"  Added to zip: {item.name}")
        print(f"  Zip created: {zip_out} ({zip_out.stat().st_size:,} bytes)")
    else:
        print("\n[Step 5] Skipped (no --zip-out specified).")

    print("\n" + "=" * 60)
    print("PACKAGING COMPLETE")
    print(f"  Output dir : {output_dir}")
    if zip_out:
        print(f"  Zip archive: {zip_out}")
    print("  STATUS: artifacts/ is NOT staged — do not run 'git add artifacts/'")
    print("  Upload the dataset folder/zip manually to Kaggle as a private dataset.")
    print("  SYNTHETIC DEMO ONLY — NOT LEGAL ADVICE — NOT OFFICIAL LEGAL TEXT")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
