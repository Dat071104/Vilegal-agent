"""
source_registry.py — Audited dataset metadata registry.

Every entry reflects the Phase 1 audit findings.
Do not add sources that have not been audited.
BULK DOWNLOAD BLOCKED for all sources.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Hard cap enforced everywhere — a human must change this constant
# deliberately after completing the Phase 2B bulk-download gates.
MAX_RECORDS_HARD_CAP: int = 100
DEFAULT_MAX_RECORDS: int = 50


@dataclass(frozen=True)
class SourceMeta:
    """Immutable metadata for an audited Vietnamese legal data source."""

    source_id: str
    """Short stable key used on the CLI, e.g. 'uts_vlc'."""

    name: str
    """Human-readable dataset name."""

    hf_handle: Optional[str]
    """Hugging Face dataset handle (owner/name), or None for non-HF sources."""

    url: str
    """Dataset card URL or source landing page."""

    license: str
    """License identifier recorded during Phase 1 audit."""

    license_confirmed: bool
    """True when the license was verified manually against the HF card."""

    attribution_required: bool
    """True when downstream use must include visible attribution."""

    attribution_note: str
    """Short attribution instruction for downstream use."""

    bulk_download_blocked: bool
    """Always True in Phase 2A. Must be flipped only after Phase 2B gates pass."""

    approved_for_sample: bool
    """True when sample-only ingestion is approved."""

    notes: str = ""
    """Audit notes and caveats."""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

REGISTRY: dict[str, SourceMeta] = {
    "uts_vlc": SourceMeta(
        source_id="uts_vlc",
        name="undertheseanlp/UTS_VLC",
        hf_handle="undertheseanlp/UTS_VLC",
        url="https://huggingface.co/datasets/undertheseanlp/UTS_VLC",
        license="MIT",
        license_confirmed=True,
        attribution_required=False,
        attribution_note="MIT license — attribution appreciated but not legally required.",
        bulk_download_blocked=True,
        approved_for_sample=True,
        notes=(
            "CONFIRMED: MIT license on HF card as of 2026-06-09. "
            "Covers Constitution, Codes (Bo luat), and Laws (Luat) 1945-2026 only. "
            "Does NOT cover decrees, circulars, or decisions. "
            "NEEDS MANUAL REVIEW: provenance and upstream relicensing basis."
        ),
    ),
    "viet_legal_instruct": SourceMeta(
        source_id="viet_legal_instruct",
        name="duyet/vietnamese-legal-instruct",
        hf_handle="duyet/vietnamese-legal-instruct",
        url="https://huggingface.co/datasets/duyet/vietnamese-legal-instruct",
        license="CC-BY-4.0",
        license_confirmed=True,
        attribution_required=True,
        attribution_note=(
            "CC-BY-4.0 — include dataset name 'duyet/vietnamese-legal-instruct' "
            "and link to https://huggingface.co/datasets/duyet/vietnamese-legal-instruct "
            "in any downstream artifact or publication."
        ),
        bulk_download_blocked=True,
        approved_for_sample=True,
        notes=(
            "CONFIRMED: CC-BY-4.0 on HF card as of 2026-06-09. "
            "Generated instruction pairs from th1nhng0/vietnamese-legal-documents. "
            "~468k pairs, 14 task types. NOT legal ground truth. "
            "NEEDS MANUAL REVIEW: upstream relicensing rights."
        ),
    ),
    "viet_legal_docs": SourceMeta(
        source_id="viet_legal_docs",
        name="th1nhng0/vietnamese-legal-documents",
        hf_handle="th1nhng0/vietnamese-legal-documents",
        url="https://huggingface.co/datasets/th1nhng0/vietnamese-legal-documents",
        license="CC-BY-4.0",
        license_confirmed=True,
        attribution_required=True,
        attribution_note=(
            "CC-BY-4.0 — include dataset name 'th1nhng0/vietnamese-legal-documents' "
            "and link to https://huggingface.co/datasets/th1nhng0/vietnamese-legal-documents "
            "in any downstream artifact or publication."
        ),
        bulk_download_blocked=True,
        approved_for_sample=True,
        notes=(
            "CONFIRMED: CC-BY-4.0 on HF card as of 2026-06-09. "
            "Broad coverage: laws and sub-law instruments sourced from vbpl.vn. "
            "NEEDS MANUAL REVIEW: provenance and relicensing basis."
        ),
    ),
    "viet_legal_qa": SourceMeta(
        source_id="viet_legal_qa",
        name="thangvip/vietnamese-legal-qa",
        hf_handle="thangvip/vietnamese-legal-qa",
        url="https://huggingface.co/datasets/thangvip/vietnamese-legal-qa",
        license="UNKNOWN",
        license_confirmed=False,
        attribution_required=False,
        attribution_note="License unresolved — do not use in downstream artifacts.",
        bulk_download_blocked=True,
        approved_for_sample=False,
        notes=(
            "NEEDS MANUAL REVIEW: license not confirmed as of 2026-06-09. "
            "Evaluation-only candidate. Do not ingest as primary training source. "
            "Do not use until license is resolved."
        ),
    ),
    "synthetic_example": SourceMeta(
        source_id="synthetic_example",
        name="Synthetic Example Fixture",
        hf_handle=None,
        url="tests/fixtures/synthetic_legal_articles.jsonl",
        license="Internal Example Only",
        license_confirmed=True,
        attribution_required=False,
        attribution_note="Synthetic fixture — no attribution required.",
        bulk_download_blocked=False,
        approved_for_sample=True,
        notes=(
            "CONFIRMED: local synthetic fixture for offline testing. "
            "Contains no real legal text. Safe for git tracking."
        ),
    ),
}


def get_source(source_id: str) -> SourceMeta:
    """Return the SourceMeta for a given source_id, raising KeyError if unknown."""
    if source_id not in REGISTRY:
        available = ", ".join(sorted(REGISTRY.keys()))
        raise KeyError(
            f"Unknown source '{source_id}'. Available sources: {available}"
        )
    return REGISTRY[source_id]


def enforce_max_records(requested: int, source_id: str = "") -> int:
    """
    Return the clamped max-records value, enforcing the hard cap.

    Raises ValueError if requested <= 0.
    Logs a warning (via print) if clamped.
    """
    if requested <= 0:
        raise ValueError(f"--max-records must be a positive integer, got {requested}.")
    if requested > MAX_RECORDS_HARD_CAP:
        label = f" for source '{source_id}'" if source_id else ""
        print(
            f"[WARN] Requested {requested} records{label} exceeds hard cap "
            f"{MAX_RECORDS_HARD_CAP}. Clamping to {MAX_RECORDS_HARD_CAP}."
        )
        return MAX_RECORDS_HARD_CAP
    return requested
