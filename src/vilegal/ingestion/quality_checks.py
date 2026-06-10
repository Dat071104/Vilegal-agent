"""
quality_checks.py — Data quality metrics for Phase 2A sample ingestion runs.

Computes the eight metrics required by docs/PHASE_2_PRE_AUDIT.md.
No network calls. No model inference. No bulk data access.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class QualityReport:
    """
    Quality metrics for a single sample ingestion run.
    Written as quality_report.json alongside every output batch.
    """

    source_dataset: str
    max_records: int
    total_seen: int
    total_normalized: int
    total_rejected: int

    # --- Computed rates (0.0–1.0) ---
    parse_success_rate: float
    """Share of raw records that normalized successfully."""

    empty_text_rate: float
    """Share of normalized records with blank or whitespace-only text."""

    duplicate_rate: float
    """Share of normalized records that are exact duplicates by record_id."""

    missing_metadata_rate: float
    """Share of normalized records missing any required provenance field."""

    missing_license_rate: float
    """Share of normalized records where license is blank or 'UNKNOWN'."""

    malformed_article_rate: float
    """Share of normalized records with non-positive or non-integer article_number."""

    bulk_download_blocked: bool = True
    """Always True in Phase 2A."""

    quality_gate_passed: bool = False
    """True when all rates are within Phase 2 pre-audit thresholds."""

    threshold_violations: list[str] = field(default_factory=list)
    """Human-readable list of threshold violations, if any."""


# Phase 2 pre-audit quality thresholds (from docs/PHASE_2_PRE_AUDIT.md)
THRESHOLDS: dict[str, tuple[str, float]] = {
    "parse_success_rate":    (">=", 0.99),
    "empty_text_rate":       ("<=", 0.005),
    "duplicate_rate":        ("<=", 0.02),
    "missing_metadata_rate": ("<=", 0.01),
    "missing_license_rate":  ("<=", 0.01),
    "malformed_article_rate":("<=", 0.01),
}

_REQUIRED_PROVENANCE = frozenset(
    ["record_id", "source_dataset", "source_url", "license", "retrieved_at", "transform_version"]
)


def _rate(numerator: int, denominator: int) -> float:
    """Safe division returning 0.0 on zero denominator."""
    return round(numerator / denominator, 6) if denominator > 0 else 0.0


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    return str(value).strip() == ""


def _record_hash(record: dict[str, Any]) -> str:
    return record.get("record_id") or hashlib.sha256(
        record.get("text", "")[:200].encode()
    ).hexdigest()[:16]


def _check_thresholds(report: QualityReport) -> tuple[bool, list[str]]:
    violations: list[str] = []
    for metric, (op, limit) in THRESHOLDS.items():
        value = getattr(report, metric)
        if op == ">=" and value < limit:
            violations.append(
                f"{metric}={value:.4f} < required {limit:.4f}"
            )
        elif op == "<=" and value > limit:
            violations.append(
                f"{metric}={value:.4f} > allowed {limit:.4f}"
            )
    return len(violations) == 0, violations


def run_quality_checks(
    normalized_records: list[dict[str, Any]],
    rejected_records: list[dict[str, Any]],
    source_dataset: str,
    max_records: int,
) -> QualityReport:
    """
    Compute all 8 quality metrics over a batch of normalized and rejected records.

    Args:
        normalized_records: Records that passed normalization.
        rejected_records:   Records that failed normalization.
        source_dataset:     Source dataset name (for the report).
        max_records:        The max_records limit used in this run.

    Returns:
        A populated QualityReport with quality_gate_passed and threshold_violations set.
    """
    total_seen = len(normalized_records) + len(rejected_records)
    total_normalized = len(normalized_records)
    total_rejected = len(rejected_records)

    # --- parse_success_rate ---
    parse_success_rate = _rate(total_normalized, total_seen)

    # --- empty_text_rate ---
    empty_text_count = sum(
        1 for r in normalized_records if _is_blank(r.get("text"))
    )
    empty_text_rate = _rate(empty_text_count, total_normalized)

    # --- duplicate_rate ---
    seen_hashes: set[str] = set()
    duplicate_count = 0
    for r in normalized_records:
        h = _record_hash(r)
        if h in seen_hashes:
            duplicate_count += 1
        seen_hashes.add(h)
    duplicate_rate = _rate(duplicate_count, total_normalized)

    # --- missing_metadata_rate ---
    missing_meta_count = sum(
        1 for r in normalized_records
        if any(_is_blank(r.get(f)) for f in _REQUIRED_PROVENANCE)
    )
    missing_metadata_rate = _rate(missing_meta_count, total_normalized)

    # --- missing_license_rate ---
    missing_license_count = sum(
        1 for r in normalized_records
        if _is_blank(r.get("license")) or str(r.get("license", "")).upper() == "UNKNOWN"
    )
    missing_license_rate = _rate(missing_license_count, total_normalized)

    # --- malformed_article_rate ---
    malformed_article_count = 0
    for r in normalized_records:
        art_num = r.get("article_number")
        if art_num is not None:
            try:
                if int(art_num) < 1:
                    malformed_article_count += 1
            except (TypeError, ValueError):
                malformed_article_count += 1
    malformed_article_rate = _rate(malformed_article_count, total_normalized)

    report = QualityReport(
        source_dataset=source_dataset,
        max_records=max_records,
        total_seen=total_seen,
        total_normalized=total_normalized,
        total_rejected=total_rejected,
        parse_success_rate=parse_success_rate,
        empty_text_rate=empty_text_rate,
        duplicate_rate=duplicate_rate,
        missing_metadata_rate=missing_metadata_rate,
        missing_license_rate=missing_license_rate,
        malformed_article_rate=malformed_article_rate,
        bulk_download_blocked=True,
    )

    gate_passed, violations = _check_thresholds(report)
    report.quality_gate_passed = gate_passed
    report.threshold_violations = violations
    return report


def write_quality_report(report: QualityReport, output_dir: Path) -> Path:
    """Serialize a QualityReport to quality_report.json in output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "quality_report.json"
    out_path.write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return out_path
