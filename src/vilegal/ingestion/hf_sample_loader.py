"""
hf_sample_loader.py — Safe record loader for Phase 2A.

Loading strategy:
  1. --offline-fixture path  → read local JSONL file only (no network).
  2. online (HF streaming)   → uses datasets.load_dataset(..., streaming=True).
                               Only takes up to max_records; never materialises
                               the full dataset on disk.

CRITICAL RULES:
  - Never call load_dataset without streaming=True.
  - Never write raw records to a git-tracked path.
  - Max records hard cap: 100 (enforced by source_registry.enforce_max_records).
  - Bulk download is BLOCKED.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator, Optional


# ---------------------------------------------------------------------------
# Offline / fixture loader
# ---------------------------------------------------------------------------

def _iter_jsonl(filepath: Path) -> Iterator[dict[str, Any]]:
    """Yield parsed dicts from a JSONL file, skipping blank lines."""
    with filepath.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_from_fixture(fixture_path: Path, max_records: int) -> list[dict[str, Any]]:
    """
    Load up to max_records records from a local JSONL fixture file.
    No network access. Safe for CI and offline environments.
    """
    if not fixture_path.exists():
        raise FileNotFoundError(f"Offline fixture not found: {fixture_path}")
    records: list[dict[str, Any]] = []
    for i, record in enumerate(_iter_jsonl(fixture_path)):
        if i >= max_records:
            break
        records.append(record)
    return records


# ---------------------------------------------------------------------------
# Online / HF streaming loader
# ---------------------------------------------------------------------------

def load_from_hf_streaming(
    hf_handle: str,
    max_records: int,
    split: str = "train",
) -> list[dict[str, Any]]:
    """
    Load up to max_records records from a HF dataset in streaming mode.

    Uses datasets.load_dataset(..., streaming=True) to avoid materialising
    the full dataset. Raises ImportError if `datasets` is not installed.
    Raises RuntimeError if the source is not reachable.
    """
    try:
        from datasets import load_dataset  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "The 'datasets' package is required for online HF loading. "
            "Install it with: pip install datasets"
        ) from exc

    records: list[dict[str, Any]] = []
    try:
        ds = load_dataset(hf_handle, split=split, streaming=True, trust_remote_code=False)
        for i, example in enumerate(ds):
            if i >= max_records:
                break
            records.append(dict(example))
    except Exception as exc:
        raise RuntimeError(
            f"Failed to stream from HF dataset '{hf_handle}' (split='{split}'): {exc}\n"
            "Tip: Use --offline-fixture to run without network access."
        ) from exc
    return records


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------

def load_records(
    hf_handle: Optional[str],
    max_records: int,
    offline_fixture: Optional[Path] = None,
    hf_split: str = "train",
) -> tuple[list[dict[str, Any]], str]:
    """
    Load up to max_records records using the appropriate strategy.

    Returns:
        (records, mode)  where mode is 'offline_fixture' or 'hf_streaming'.

    If offline_fixture is provided, it is always used regardless of network.
    """
    if offline_fixture is not None:
        return load_from_fixture(offline_fixture, max_records), "offline_fixture"

    if hf_handle is None:
        raise ValueError(
            "No offline_fixture provided and no hf_handle configured for this source. "
            "Use --offline-fixture to specify a local JSONL file."
        )

    records = load_from_hf_streaming(hf_handle, max_records, split=hf_split)
    return records, "hf_streaming"
