"""
normalizers.py — Raw record normalization for Phase 2A sample ingestion.

Maps heterogeneous raw dicts (from HF datasets or local JSONL fixtures) into
a canonical flat normalized record dict that satisfies the provenance contract.

IMPORTANT: No scraping, no bulk download, no model training code here.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Optional

from vilegal.data_contracts import DocumentType, SourceStatus

TRANSFORM_VERSION = "phase_2a_v1"

# Required fields in every normalized record
REQUIRED_FIELDS = frozenset(
    ["record_id", "source_dataset", "license", "retrieved_at",
     "transform_version", "text"]
)


def _safe_str(value: Any, default: str = "") -> str:
    """Coerce a value to stripped string, returning default if None/empty."""
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


def _coerce_doc_type(raw: Any) -> str:
    """Normalize a raw document type string to a DocumentType enum value, or 'other'."""
    if raw is None:
        return DocumentType.OTHER.value
    raw_str = str(raw).strip().lower()
    for member in DocumentType:
        if member.value == raw_str:
            return member.value
    return DocumentType.OTHER.value


def _coerce_status(raw: Any) -> str:
    """Normalize a raw status string to a SourceStatus enum value, or 'unknown'."""
    if raw is None:
        return SourceStatus.UNKNOWN.value
    raw_str = str(raw).strip().lower()
    for member in SourceStatus:
        if member.value == raw_str:
            return member.value
    return SourceStatus.UNKNOWN.value


def _make_record_id(source_dataset: str, source_id: str, text: str) -> str:
    """Deterministic record ID: sha256 of source_dataset + source_id + text[:200]."""
    digest_input = f"{source_dataset}|{source_id}|{text[:200]}"
    return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()[:16]


def normalize_record(
    raw: dict[str, Any],
    source_dataset: str,
    source_url: str,
    license_str: str,
    retrieved_at: Optional[str] = None,
) -> dict[str, Any]:
    """
    Map a raw dict to a canonical normalized record.

    Returns a flat dict with all required provenance and content fields.
    Raises ValueError if the record cannot be normalized (e.g., blank text).
    """
    if retrieved_at is None:
        retrieved_at = datetime.now(tz=timezone.utc).isoformat()

    # --- Core text extraction ---
    text = _safe_str(
        raw.get("text")
        or raw.get("article_text")
        or raw.get("content")
        or raw.get("output")  # instruction-pair format
    )
    if not text:
        raise ValueError("Record has no usable text field.")

    # --- Source provenance ---
    source_id = _safe_str(
        raw.get("source_id")
        or raw.get("doc_id")
        or raw.get("id")
        or raw.get("_id"),
        default="UNKNOWN",
    )

    record_id = _make_record_id(source_dataset, source_id, text)

    # --- Document metadata ---
    document_type = _coerce_doc_type(
        raw.get("doc_type") or raw.get("type") or raw.get("document_type")
    )
    document_number = _safe_str(
        raw.get("number") or raw.get("doc_number") or raw.get("law_number")
    )
    title = _safe_str(
        raw.get("title")
        or raw.get("document_title")
        or raw.get("name")
        or raw.get("instruction")  # instruction-pair fallback
    )

    # --- Article / clause ---
    article_number_raw = raw.get("article_number") or raw.get("article_no")
    try:
        article_number: Optional[int] = int(article_number_raw) if article_number_raw is not None else None
    except (TypeError, ValueError):
        article_number = None

    clause_number = _safe_str(raw.get("clause_number") or raw.get("khoan"))

    # --- Effective status ---
    effective_status = _coerce_status(raw.get("status") or raw.get("effective_status"))

    # --- Raw metadata passthrough (exclude large/binary blobs) ---
    raw_metadata: dict[str, Any] = {
        k: v for k, v in raw.items()
        if k not in ("text", "article_text", "content", "output", "input")
        and not isinstance(v, (bytes, bytearray))
        and not (isinstance(v, str) and len(v) > 2000)
    }

    return {
        "record_id": record_id,
        "source_dataset": source_dataset,
        "source_url": source_url,
        "source_id": source_id,
        "license": license_str,
        "retrieved_at": retrieved_at,
        "transform_version": TRANSFORM_VERSION,
        "document_type": document_type,
        "document_number": document_number,
        "title": title,
        "article_number": article_number,
        "clause_number": clause_number or None,
        "text": text,
        "effective_status": effective_status,
        "raw_metadata": raw_metadata,
    }
