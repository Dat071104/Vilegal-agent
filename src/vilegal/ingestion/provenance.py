"""
provenance.py — Provenance manifest builder and writer.

Tracks source-level provenance for every sample ingestion run.
Bulk download is always blocked in Phase 2A.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from vilegal.ingestion.source_registry import MAX_RECORDS_HARD_CAP, SourceMeta


@dataclass
class ProvenanceManifest:
    """
    Source-level provenance for a sample ingestion run.
    Written as provenance_manifest.json alongside every output batch.
    """

    source_dataset: str
    """Dataset handle or name."""

    dataset_url: str
    """Dataset card URL or file path."""

    license: str
    """License identifier recorded during Phase 1 audit."""

    license_confirmed: bool
    """True when license was manually verified."""

    attribution_required: bool
    """True when downstream use requires visible attribution."""

    attribution_note: str
    """Short attribution instruction."""

    retrieved_at: str
    """ISO-8601 UTC timestamp of this ingestion run."""

    max_records: int
    """Number of records requested for this run."""

    actual_records_seen: int
    """Number of raw records actually loaded from the source."""

    bulk_download_blocked: bool = True
    """Always True in Phase 2A — do not change without Phase 2B gate approval."""

    offline_fixture_used: Optional[str] = None
    """Path to offline fixture if --offline-fixture was specified."""

    notes: str = (
        "Sample-only ingestion. This is NOT a redistribution of legal data. "
        "No bulk download was performed. Records are for pipeline validation only."
    )

    transform_version: str = "phase_2a_v1"
    """Schema transform version for this run."""


def build_manifest(
    source: SourceMeta,
    max_records: int,
    actual_records_seen: int,
    offline_fixture: Optional[Path] = None,
) -> ProvenanceManifest:
    """Construct a ProvenanceManifest from a SourceMeta and run parameters."""
    return ProvenanceManifest(
        source_dataset=source.name,
        dataset_url=source.url,
        license=source.license,
        license_confirmed=source.license_confirmed,
        attribution_required=source.attribution_required,
        attribution_note=source.attribution_note,
        retrieved_at=datetime.now(tz=timezone.utc).isoformat(),
        max_records=max_records,
        actual_records_seen=actual_records_seen,
        bulk_download_blocked=True,
        offline_fixture_used=str(offline_fixture) if offline_fixture else None,
    )


def write_manifest(manifest: ProvenanceManifest, output_dir: Path) -> Path:
    """Serialize a ProvenanceManifest to provenance_manifest.json in output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "provenance_manifest.json"
    out_path.write_text(
        json.dumps(asdict(manifest), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return out_path
