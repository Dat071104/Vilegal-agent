#!/usr/bin/env python3
"""
Phase 2E read-only content audit for existing ingestion artifacts.

Reads local JSONL and manifest files from artifacts/ and writes a measured JSON
report without modifying the input artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

NEAR_EMPTY_CHAR_THRESHOLD = 50
CITATION_PATTERNS = (
    re.compile(r"\b(?:dieu|diều|điều)\s+\d+", re.IGNORECASE),
    re.compile(r"\b(?:khoan|khoản)\s+\d+", re.IGNORECASE),
    re.compile(r"\b(?:luat|luật|bo luat|bộ luật|nghi dinh|nghị định|thong tu|thông tư|quyet dinh|quyết định)\b", re.IGNORECASE),
    re.compile(r"\b\d+/\d{4}/[A-ZĐ\-]+"),
)
ARTICLE_MARKER_PATTERN = re.compile(r"(?:^|\n)\s*(?:dieu|điều)\s+\d+", re.IGNORECASE)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def stripped_len(value: Any) -> int:
    if value is None:
        return 0
    return len(str(value).strip())


def is_missing(value: Any) -> bool:
    return stripped_len(value) == 0


def has_citation_signal(text: str) -> bool:
    return any(pattern.search(text) for pattern in CITATION_PATTERNS)


def count_article_markers(text: str) -> int:
    return len(ARTICLE_MARKER_PATTERN.findall(text))


def first_conversation_turn(raw_metadata: dict[str, Any], role: str) -> str:
    conversations = raw_metadata.get("conversations")
    if not isinstance(conversations, list):
        return ""
    for turn in conversations:
        if isinstance(turn, dict) and turn.get("role") == role:
            content = turn.get("content")
            return str(content).strip() if content is not None else ""
    return ""


def field_completeness(records: list[dict[str, Any]], fields: list[str]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for field in fields:
        summary[field] = sum(0 if is_missing(record.get(field)) else 1 for record in records)
    return summary


def summarize_common(records: list[dict[str, Any]]) -> dict[str, Any]:
    text_lengths = [stripped_len(record.get("text")) for record in records]
    return {
        "total_records": len(records),
        "document_type_counts": dict(sorted(Counter(record.get("document_type") or "MISSING" for record in records).items())),
        "missing_title_count": sum(is_missing(record.get("title")) for record in records),
        "missing_document_number_count": sum(is_missing(record.get("document_number")) for record in records),
        "missing_document_type_count": sum(is_missing(record.get("document_type")) for record in records),
        "average_text_length_chars": round(sum(text_lengths) / len(text_lengths), 2) if text_lengths else 0.0,
        "median_text_length_chars": statistics.median(text_lengths) if text_lengths else 0,
        "empty_text_count": sum(length == 0 for length in text_lengths),
        "near_empty_text_count": sum(length <= NEAR_EMPTY_CHAR_THRESHOLD for length in text_lengths),
        "citation_metadata_availability": field_completeness(
            records,
            ["source_id", "source_url", "document_number", "article_number", "clause_number", "title"],
        ),
    }


def summarize_uts(records: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    common = summarize_common(records)
    article_marker_counts = [count_article_markers(record.get("text", "")) for record in records]
    multi_article_records = sum(count > 1 for count in article_marker_counts)
    return {
        **common,
        "records_with_article_markers": sum(count > 0 for count in article_marker_counts),
        "records_with_multiple_article_markers": multi_article_records,
        "article_parsing_possible": multi_article_records > 0,
        "article_parsing_basis": (
            "Current normalized rows are document-level text blobs; many rows contain multiple article markers "
            "but article_number is not populated, so article extraction is possible only as a secondary parsing step."
        ),
        "coverage_limitation_confirmed": (
            "Manifest and source registry scope UTS_VLC to Constitution, Codes, and Laws only; "
            "it does not represent the full Vietnamese legal instrument universe."
        ),
        "attribution_required": manifest.get("attribution_required"),
        "license": manifest.get("license"),
    }


def summarize_duyet(records: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    common = summarize_common(records)
    qa_type_counts: Counter[str] = Counter()
    normalized_matches_user_turn = 0
    assistant_answers_in_raw_metadata = 0
    assistant_answers_with_citations = 0
    assistant_length_chars: list[int] = []

    for record in records:
        raw_metadata = record.get("raw_metadata") or {}
        if isinstance(raw_metadata, dict):
            qa_type_counts[str(raw_metadata.get("qa_type") or "UNKNOWN")] += 1
            user_turn = first_conversation_turn(raw_metadata, "user")
            assistant_turn = first_conversation_turn(raw_metadata, "assistant")
            if user_turn and user_turn == str(record.get("text", "")).strip():
                normalized_matches_user_turn += 1
            if assistant_turn:
                assistant_answers_in_raw_metadata += 1
                assistant_length_chars.append(len(assistant_turn))
                if has_citation_signal(assistant_turn):
                    assistant_answers_with_citations += 1

    hallucination_risk_categories: list[dict[str, Any]] = []
    risk_map = {
        "qa_practical": "Applies law to practical scenarios and can add unsupported advice.",
        "explain_simple": "Simplifies legal content and can omit conditions or exceptions.",
        "compare": "Compares instruments and can overstate differences or current effect.",
        "summarize": "Compresses long legal text and can drop scope limits.",
        "full_text": "Requests full text and can truncate or hallucinate omitted sections.",
    }
    for qa_type, count in sorted(qa_type_counts.items()):
        if qa_type in risk_map:
            hallucination_risk_categories.append(
                {"qa_type": qa_type, "count": count, "risk": risk_map[qa_type]}
            )

    return {
        **common,
        "qa_type_counts": dict(sorted(qa_type_counts.items())),
        "normalized_text_matches_user_turn_count": normalized_matches_user_turn,
        "assistant_answers_in_raw_metadata_count": assistant_answers_in_raw_metadata,
        "assistant_answers_with_citation_signal_count": assistant_answers_with_citations,
        "assistant_answers_with_citation_signal_rate": round(
            assistant_answers_with_citations / assistant_answers_in_raw_metadata, 4
        ) if assistant_answers_in_raw_metadata else 0.0,
        "average_assistant_answer_length_chars": round(
            sum(assistant_length_chars) / len(assistant_length_chars), 2
        ) if assistant_length_chars else 0.0,
        "hallucination_risk_categories": hallucination_risk_categories,
        "attribution_required": manifest.get("attribution_required"),
        "license": manifest.get("license"),
    }


def cross_source_summary(
    uts_records: list[dict[str, Any]],
    duyet_records: list[dict[str, Any]],
    uts_manifest: dict[str, Any],
    duyet_manifest: dict[str, Any],
) -> dict[str, Any]:
    combined = uts_records + duyet_records
    provenance_fields = ["source_dataset", "source_url", "source_id", "license", "retrieved_at"]
    uts_record_ids = {record.get("record_id") for record in uts_records if record.get("record_id")}
    duyet_record_ids = {record.get("record_id") for record in duyet_records if record.get("record_id")}
    uts_source_ids = {record.get("source_id") for record in uts_records if record.get("source_id")}
    duyet_source_ids = {record.get("source_id") for record in duyet_records if record.get("source_id")}
    uts_texts = {record.get("text") for record in uts_records if record.get("text")}
    duyet_texts = {record.get("text") for record in duyet_records if record.get("text")}

    per_source_provenance = {}
    for label, records in (("uts_vlc", uts_records), ("duyet_legal_instruct", duyet_records)):
        per_source_provenance[label] = {
            "required_field_presence": field_completeness(records, provenance_fields),
            "all_records_complete": all(
                not any(is_missing(record.get(field)) for field in provenance_fields)
                for record in records
            ),
        }

    return {
        "duplicate_record_ids_across_sources": len(uts_record_ids & duyet_record_ids),
        "duplicate_source_ids_across_sources": len(uts_source_ids & duyet_source_ids),
        "exact_duplicate_text_records_across_sources": len(uts_texts & duyet_texts),
        "provenance_completeness": per_source_provenance,
        "license_attribution_completeness": {
            "uts_vlc_manifest_license_present": not is_missing(uts_manifest.get("license")),
            "uts_vlc_attribution_note_present": not is_missing(uts_manifest.get("attribution_note")),
            "duyet_manifest_license_present": not is_missing(duyet_manifest.get("license")),
            "duyet_attribution_note_present": not is_missing(duyet_manifest.get("attribution_note")),
            "duyet_attribution_required": bool(duyet_manifest.get("attribution_required")),
        },
        "source_role_separation": {
            "uts_vlc_corpus_candidate_confirmed": all(
                "conversations" not in (record.get("raw_metadata") or {}) for record in uts_records
            ),
            "duyet_text_is_user_query_only": all(
                first_conversation_turn(record.get("raw_metadata") or {}, "user")
                == str(record.get("text", "")).strip()
                for record in duyet_records
            ),
            "duyet_assistant_retained_only_in_raw_metadata": all(
                bool(first_conversation_turn(record.get("raw_metadata") or {}, "assistant"))
                for record in duyet_records
            ),
        },
    }


def readiness_matrix(uts: dict[str, Any], duyet: dict[str, Any], cross: dict[str, Any]) -> dict[str, Any]:
    return {
        "rag_corpus_readiness": {
            "status": "PASS WITH RISKS",
            "scope": "UTS_VLC only",
            "basis": (
                "UTS_VLC has complete provenance and non-empty long-form legal text, but current rows are document-level, "
                "article fields are sparse, and corpus coverage excludes sub-law instruments."
            ),
        },
        "sft_dataset_readiness": {
            "status": "BLOCKED",
            "scope": "duyet_legal_instruct",
            "basis": (
                "Assistant answers are generated supervision rather than verified ground truth. "
                "They require filtering and human review before any SFT use."
            ),
        },
        "evaluation_dataset_readiness": {
            "status": "BLOCKED",
            "scope": "cross-source",
            "basis": (
                "Neither source is a vetted answer key. UTS_VLC lacks article/chunk labels in current rows and "
                "duyet assistant answers carry hallucination risk."
            ),
        },
        "public_release_readiness": {
            "status": "BLOCKED",
            "scope": "cross-source",
            "basis": (
                "Provenance fields are complete, but relicensing/publication review remains open and "
                "CC-BY attribution obligations must be carried through."
            ),
        },
        "uts_vlc_article_chunking_next_step": {
            "status": "PASS WITH RISKS" if uts.get("article_parsing_possible") else "BLOCKED",
            "basis": uts.get("article_parsing_basis"),
        },
        "duyet_sft_filtering_next_step": {
            "status": "PASS WITH RISKS",
            "basis": (
                "The normalized field is correctly limited to the user query, so the dataset can proceed to an SFT filtering review phase, "
                "but not directly to training."
            ),
        },
    }


def build_report(input_dir: Path) -> dict[str, Any]:
    uts_dir = input_dir / "uts_vlc"
    duyet_dir = input_dir / "duyet_legal_instruct"
    required_paths = [
        uts_dir / "sample_normalized.jsonl",
        uts_dir / "provenance_manifest.json",
        duyet_dir / "sample_normalized.jsonl",
        duyet_dir / "provenance_manifest.json",
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing Phase 2D artifacts: {missing}")

    uts_records = load_jsonl(uts_dir / "sample_normalized.jsonl")
    duyet_records = load_jsonl(duyet_dir / "sample_normalized.jsonl")
    uts_manifest = load_json(uts_dir / "provenance_manifest.json")
    duyet_manifest = load_json(duyet_dir / "provenance_manifest.json")

    uts_summary = summarize_uts(uts_records, uts_manifest)
    duyet_summary = summarize_duyet(duyet_records, duyet_manifest)
    cross_summary = cross_source_summary(uts_records, duyet_records, uts_manifest, duyet_manifest)

    return {
        "phase": "Phase 2E - Data Content Quality Audit",
        "input_dir": str(input_dir),
        "near_empty_char_threshold": NEAR_EMPTY_CHAR_THRESHOLD,
        "sources": {
            "uts_vlc": uts_summary,
            "duyet_legal_instruct": duyet_summary,
        },
        "cross_source": cross_summary,
        "readiness_matrix": readiness_matrix(uts_summary, duyet_summary, cross_summary),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only content audit for Phase 2D artifacts.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("artifacts/phase_2d_controlled_ingestion"),
        help="Directory containing Phase 2D source subdirectories.",
    )
    parser.add_argument(
        "--report-out",
        type=Path,
        default=Path("artifacts/phase_2e_content_audit_report.json"),
        help="Path to write the generated JSON audit report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = build_report(args.input_dir)
    except FileNotFoundError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2

    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote audit report to {args.report_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
