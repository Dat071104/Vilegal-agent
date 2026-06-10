#!/usr/bin/env python3
"""
Phase 2L CLI for checking Phase 3 readiness without starting Phase 3.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from vilegal.ingestion.readiness_gate import check_phase3_readiness, report_to_dict  # noqa: E402


def resolve_artifacts_root() -> Path:
    return (ROOT / "artifacts").resolve()


def ensure_path_within_artifacts(path: Path) -> Path:
    resolved = path.resolve()
    artifacts_root = resolve_artifacts_root()
    if resolved != artifacts_root and artifacts_root not in resolved.parents:
        raise ValueError(f"Path must stay under artifacts/: {resolved}")
    return resolved


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Phase 3 readiness without generating QA, fine-tuning, or RAG indexes.")
    parser.add_argument("--manifest-dir", type=Path, required=True)
    parser.add_argument("--report-out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest_dir = ensure_path_within_artifacts(args.manifest_dir)
        report_out = ensure_path_within_artifacts(args.report_out)
        report = check_phase3_readiness(
            manifest_dir=manifest_dir,
            attribution_path=ROOT / "docs" / "ATTRIBUTION.md",
            data_use_policy_path=ROOT / "docs" / "DATA_USE_POLICY.md",
            phase2j_doc_path=ROOT / "docs" / "PHASE_2J_REVIEW_RESULTS_AUDIT.md",
            phase2k_doc_path=ROOT / "docs" / "PHASE_2K_CORPUS_CANDIDATE_MANIFEST.md",
        )
        write_json(report_out, report_to_dict(report))
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Report written to: {report_out}")
    print(f"Readiness verdict: {report.readiness_verdict}")
    print(f"Corpus candidate manifest ready: {report.corpus_candidate_manifest_ready}")
    print(f"Phase 3 scaffold ready: {report.phase3_scaffold_ready}")
    print(f"QA generation ready: {report.qa_generation_ready}")
    print(f"Fine-tuning ready: {report.fine_tuning_ready}")
    print(f"RAG indexing ready: {report.rag_indexing_ready}")
    return 0 if report.readiness_verdict != "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
