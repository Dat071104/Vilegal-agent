#!/usr/bin/env python3
"""
Validate the Phase 3A Kaggle/QLoRA scaffold without training or model downloads.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.training import validate_phase3a_scaffold  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the Phase 3A scaffold-only config, notebook, and docs.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "phase3a_qlora_scaffold.yaml",
        help="Path to the Phase 3A scaffold config.",
    )
    parser.add_argument(
        "--notebook",
        type=Path,
        default=ROOT / "notebooks" / "phase3a_kaggle_qlora_scaffold.ipynb",
        help="Path to the Phase 3A scaffold notebook.",
    )
    parser.add_argument(
        "--docs",
        type=Path,
        default=ROOT / "docs" / "PHASE_3A_KAGGLE_QLORA_SCAFFOLD.md",
        help="Path to the Phase 3A scaffold documentation.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = validate_phase3a_scaffold(
            config_path=args.config,
            notebook_path=args.notebook,
            docs_path=args.docs,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"Phase 3A scaffold validation FAILED: {exc}", file=sys.stderr)
        return 1

    print("Phase 3A scaffold validation PASS")
    print(f"Config: {args.config}")
    print(f"Notebook: {report.notebook_path}")
    print(f"Docs: {report.docs_path}")
    print("Scaffold-only boundary preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
