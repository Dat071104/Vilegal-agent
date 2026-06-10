"""
article_filter.py - Phase 2G deterministic filtering for UTS article candidates.

Filters parser-derived article/chunk candidates into transparent review buckets.
This module does not approve any candidate for RAG and does not promote any
candidate to legal ground truth.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

MIN_TEXT_CHARS = 80
MIN_WORD_COUNT = 12
SUSPICIOUS_SHORT_TEXT_CHARS = 100
SUSPICIOUS_LONG_TEXT_CHARS = 50000

DECISION_REJECT_EMPTY = "reject_empty"
DECISION_REJECT_NEAR_EMPTY = "reject_near_empty"
DECISION_REJECT_DUPLICATE_HASH = "reject_duplicate_hash"
DECISION_REJECT_MISSING_PARENT_PROVENANCE = "reject_missing_parent_provenance"
DECISION_REJECT_MISSING_REQUIRED_TEXT = "reject_missing_required_text"
DECISION_REJECT_MISSING_REQUIRED_HASH = "reject_missing_required_hash"
DECISION_NEEDS_REVIEW_SUSPICIOUS_LENGTH = "needs_review_suspicious_length"
DECISION_NEEDS_REVIEW_PREAMBLE = "needs_review_preamble_or_header_noise"
DECISION_NEEDS_REVIEW_MARKER = "needs_review_marker_uncertainty"
DECISION_KEEP = "keep_candidate_for_human_review"

REQUIRED_PARENT_FIELDS = (
    "parent_record_id",
    "source_dataset",
    "source_id",
    "source_url",
    "license",
    "retrieved_at",
)


@dataclass
class FilterMetrics:
    total_input_candidates: int
    total_output_records: int
    total_rejected: int
    total_needs_review: int
    total_keep_candidate_for_human_review: int
    rejected_by_reason: dict[str, int]
    needs_review_by_reason: dict[str, int]
    duplicate_hash_groups: int
    duplicate_candidates_rejected: int
    parent_document_warning_count: int
    missing_required_fields_count: int
    empty_count: int
    near_empty_count: int
    suspicious_length_count: int
    preamble_warning_count: int
    marker_uncertainty_count: int
    parent_provenance_coverage: float
    approved_for_rag_index_true_count: int
    is_legal_ground_truth_true_count: int
    safety_verdict: str


@dataclass
class FilterReport:
    phase: str
    filter_version: str
    input_dir: str
    output_dir: str
    source_manifest_path: str
    status: str
    blocked: bool
    reason: str
    metrics: FilterMetrics
    duplicate_group_sizes: dict[str, int] = field(default_factory=dict)
    missing_required_fields: list[str] = field(default_factory=list)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def is_blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def stripped_len(value: Any) -> int:
    return len(str(value).strip()) if value is not None else 0


def word_count(text: str) -> int:
    return len([part for part in text.strip().split() if part])


def candidate_hash(candidate: dict[str, Any]) -> str:
    existing = candidate.get("article_hash") or candidate.get("text_hash")
    if not is_blank(existing):
        return str(existing)
    text = str(candidate.get("text") or "").strip()
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def make_candidate_id(candidate: dict[str, Any], article_hash: str) -> str:
    digest_input = "|".join(
        [
            str(candidate.get("parent_record_id") or ""),
            str(candidate.get("source_id") or ""),
            str(candidate.get("article_number") or ""),
            str(candidate.get("chunk_index") or ""),
            article_hash,
        ]
    )
    return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()[:16]


def normalize_warning_index(warnings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for warning in warnings:
        parent_record_id = str(warning.get("parent_record_id") or "")
        if parent_record_id:
            index[parent_record_id].append(warning)
    for key in index:
        index[key] = sorted(index[key], key=lambda item: (str(item.get("code") or ""), str(item.get("message") or "")))
    return dict(index)


def parent_missing_fields(candidate: dict[str, Any]) -> list[str]:
    return [field for field in REQUIRED_PARENT_FIELDS if is_blank(candidate.get(field))]


def normalize_candidate(candidate: dict[str, Any], warning_index: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    article_hash = candidate_hash(candidate)
    normalized = dict(candidate)
    normalized["input_index"] = int(candidate.get("input_index") or 0)
    normalized["article_hash"] = article_hash
    normalized["candidate_id"] = make_candidate_id(candidate, article_hash)
    normalized["text_char_count"] = stripped_len(candidate.get("text"))
    normalized["text_word_count"] = word_count(str(candidate.get("text") or ""))
    parent_warnings = warning_index.get(str(candidate.get("parent_record_id") or ""), [])
    normalized["parent_document_warning_codes"] = [str(item.get("code") or "") for item in parent_warnings]
    normalized["parent_document_warning_messages"] = [str(item.get("message") or "") for item in parent_warnings]
    normalized["risk_flags"] = []
    normalized["filter_reasons"] = []
    normalized["duplicate_of"] = None
    normalized["approved_for_rag_index"] = False
    normalized["is_legal_ground_truth"] = False
    return normalized


def select_canonical_duplicates(candidates: list[dict[str, Any]]) -> dict[str, tuple[int, str]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        article_hash = str(candidate.get("article_hash") or "")
        if article_hash:
            groups[article_hash].append(candidate)
    canonical: dict[str, tuple[int, str]] = {}
    for article_hash, group in groups.items():
        group_sorted = sorted(group, key=lambda item: int(item.get("input_index") or 0))
        canonical[article_hash] = (int(group_sorted[0].get("input_index") or 0), str(group_sorted[0]["candidate_id"]))
    return canonical


def classify_candidate(candidate: dict[str, Any], canonical_by_hash: dict[str, tuple[int, str]]) -> dict[str, Any]:
    reasons: list[str] = []
    risk_flags: list[str] = []
    missing_fields = parent_missing_fields(candidate)
    if missing_fields:
        reasons.append(DECISION_REJECT_MISSING_PARENT_PROVENANCE)
        risk_flags.extend([f"missing_{field}" for field in missing_fields])

    text = str(candidate.get("text") or "").strip()
    if "text" not in candidate:
        reasons.append(DECISION_REJECT_MISSING_REQUIRED_TEXT)
        risk_flags.append("missing_text_field")
    elif not text:
        reasons.append(DECISION_REJECT_EMPTY)
        risk_flags.append("empty_text")

    article_hash = str(candidate.get("article_hash") or "").strip()
    if not article_hash:
        reasons.append(DECISION_REJECT_MISSING_REQUIRED_HASH)
        risk_flags.append("missing_article_hash")

    text_char_count = int(candidate.get("text_char_count") or 0)
    text_word_count = int(candidate.get("text_word_count") or 0)
    canonical_entry = canonical_by_hash.get(article_hash)
    if article_hash and canonical_entry and int(candidate.get("input_index") or 0) != canonical_entry[0]:
        reasons.append(DECISION_REJECT_DUPLICATE_HASH)
        risk_flags.append("duplicate_hash_loser")
        candidate["duplicate_of"] = canonical_entry[1]

    if text and (text_char_count < MIN_TEXT_CHARS or text_word_count < MIN_WORD_COUNT):
        reasons.append(DECISION_REJECT_NEAR_EMPTY)
        risk_flags.append("near_empty_text")

    parse_flags = [str(flag) for flag in candidate.get("parse_flags") or []]
    uncertain_parse = bool(candidate.get("uncertain_parse"))

    if text and (text_char_count < SUSPICIOUS_SHORT_TEXT_CHARS or text_char_count > SUSPICIOUS_LONG_TEXT_CHARS):
        reasons.append(DECISION_NEEDS_REVIEW_SUSPICIOUS_LENGTH)
        risk_flags.append("suspicious_length_text")

    if "markdown_heading_marker" in parse_flags or text.lstrip().startswith("#"):
        reasons.append(DECISION_NEEDS_REVIEW_PREAMBLE)
        risk_flags.append("candidate_header_noise")

    if uncertain_parse or any(flag in {"article_title_missing", "article_number_unparsed"} for flag in parse_flags):
        reasons.append(DECISION_NEEDS_REVIEW_MARKER)
        risk_flags.append("marker_uncertainty")

    for code in candidate.get("parent_document_warning_codes") or []:
        risk_flags.append(f"parent_document_warning:{code}")

    reject_reasons = [
        DECISION_REJECT_MISSING_PARENT_PROVENANCE,
        DECISION_REJECT_MISSING_REQUIRED_TEXT,
        DECISION_REJECT_EMPTY,
        DECISION_REJECT_NEAR_EMPTY,
        DECISION_REJECT_MISSING_REQUIRED_HASH,
        DECISION_REJECT_DUPLICATE_HASH,
    ]
    if any(reason in reject_reasons for reason in reasons):
        decision = next(reason for reason in reasons if reason in reject_reasons)
    elif reasons:
        decision = reasons[0]
    else:
        decision = DECISION_KEEP

    candidate["filter_decision"] = decision
    candidate["filter_reasons"] = sorted(set(reasons or [DECISION_KEEP]))
    candidate["risk_flags"] = sorted(set(risk_flags))
    candidate["approved_for_rag_index"] = False
    candidate["is_legal_ground_truth"] = False
    return candidate


def build_counts(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(item.get(key) or "") for item in records if item.get(key))
    return dict(sorted(counter.items()))


def classify_candidates(
    candidates: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    warning_index = normalize_warning_index(warnings)
    normalized = [normalize_candidate({**candidate, "input_index": index}, warning_index) for index, candidate in enumerate(candidates)]
    canonical_by_hash = select_canonical_duplicates(normalized)
    decided = [classify_candidate(candidate, canonical_by_hash) for candidate in normalized]
    decided.sort(key=lambda item: str(item.get("candidate_id") or ""))

    rejected = [item for item in decided if str(item.get("filter_decision", "")).startswith("reject_")]
    needs_review = [
        item
        for item in decided
        if str(item.get("filter_decision", "")).startswith("needs_review_")
    ]
    keep = [item for item in decided if item.get("filter_decision") == DECISION_KEEP]

    duplicate_group_sizes: dict[str, int] = {}
    groups = Counter(str(item.get("article_hash") or "") for item in decided if item.get("article_hash"))
    for digest, count in sorted(groups.items()):
        if digest and count > 1:
            duplicate_group_sizes[digest] = count
    return decided, rejected, needs_review, duplicate_group_sizes


def compute_metrics(
    input_candidates: list[dict[str, Any]],
    all_records: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    needs_review: list[dict[str, Any]],
    duplicate_group_sizes: dict[str, int],
    parent_document_warning_count: int,
) -> FilterMetrics:
    keep_count = sum(1 for record in all_records if record.get("filter_decision") == DECISION_KEEP)
    missing_prov = sum(
        1 for record in all_records if record.get("filter_decision") == DECISION_REJECT_MISSING_PARENT_PROVENANCE
    )
    empty_count = sum(1 for record in all_records if not str(record.get("text") or "").strip())
    near_empty_count = sum(
        1
        for record in all_records
        if str(record.get("text") or "").strip()
        and (
            int(record.get("text_char_count") or 0) < MIN_TEXT_CHARS
            or int(record.get("text_word_count") or 0) < MIN_WORD_COUNT
        )
    )
    suspicious_length_count = sum(
        1
        for record in all_records
        if int(record.get("text_char_count") or 0) < SUSPICIOUS_SHORT_TEXT_CHARS
        or int(record.get("text_char_count") or 0) > SUSPICIOUS_LONG_TEXT_CHARS
    )
    preamble_warning_count = sum(
        1 for record in all_records if DECISION_NEEDS_REVIEW_PREAMBLE in (record.get("filter_reasons") or [])
    )
    marker_uncertainty_count = sum(
        1 for record in all_records if DECISION_NEEDS_REVIEW_MARKER in (record.get("filter_reasons") or [])
    )
    approved_true = sum(1 for record in all_records if bool(record.get("approved_for_rag_index")) is True)
    ground_truth_true = sum(1 for record in all_records if bool(record.get("is_legal_ground_truth")) is True)
    coverage = 0.0 if not all_records else round(
        sum(1 for record in all_records if not parent_missing_fields(record)) / len(all_records),
        6,
    )
    rejected_by_reason = build_counts(rejected, "filter_decision")
    needs_review_by_reason = build_counts(needs_review, "filter_decision")
    duplicate_candidates_rejected = sum(max(count - 1, 0) for count in duplicate_group_sizes.values())

    counts_reconcile = len(input_candidates) == len(all_records) == len(rejected) + len(needs_review) + keep_count
    if not counts_reconcile or coverage < 1.0 or approved_true > 0 or ground_truth_true > 0:
        verdict = "FAIL"
    elif needs_review or duplicate_group_sizes or suspicious_length_count or preamble_warning_count:
        verdict = "PASS WITH RISKS"
    else:
        verdict = "PASS"

    return FilterMetrics(
        total_input_candidates=len(input_candidates),
        total_output_records=len(all_records),
        total_rejected=len(rejected),
        total_needs_review=len(needs_review),
        total_keep_candidate_for_human_review=keep_count,
        rejected_by_reason=rejected_by_reason,
        needs_review_by_reason=needs_review_by_reason,
        duplicate_hash_groups=len(duplicate_group_sizes),
        duplicate_candidates_rejected=duplicate_candidates_rejected,
        parent_document_warning_count=parent_document_warning_count,
        missing_required_fields_count=missing_prov,
        empty_count=empty_count,
        near_empty_count=near_empty_count,
        suspicious_length_count=suspicious_length_count,
        preamble_warning_count=preamble_warning_count,
        marker_uncertainty_count=marker_uncertainty_count,
        parent_provenance_coverage=coverage,
        approved_for_rag_index_true_count=approved_true,
        is_legal_ground_truth_true_count=ground_truth_true,
        safety_verdict=verdict,
    )


def build_report(
    *,
    input_dir: Path,
    output_dir: Path,
    source_manifest_path: Path,
    reason: str,
    metrics: FilterMetrics,
    blocked: bool = False,
    missing_required_fields: list[str] | None = None,
    duplicate_group_sizes: dict[str, int] | None = None,
) -> FilterReport:
    return FilterReport(
        phase="Phase 2G - UTS Article Candidate Filtering Rules",
        filter_version="phase_2g_v1",
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        source_manifest_path=str(source_manifest_path),
        status=metrics.safety_verdict,
        blocked=blocked,
        reason=reason,
        metrics=metrics,
        duplicate_group_sizes=duplicate_group_sizes or {},
        missing_required_fields=sorted(set(missing_required_fields or [])),
    )


def as_report_dict(report: FilterReport) -> dict[str, Any]:
    return {
        "phase": report.phase,
        "filter_version": report.filter_version,
        "input_dir": report.input_dir,
        "output_dir": report.output_dir,
        "source_manifest_path": report.source_manifest_path,
        "status": report.status,
        "blocked": report.blocked,
        "reason": report.reason,
        "metrics": asdict(report.metrics),
        "duplicate_group_sizes": report.duplicate_group_sizes,
        "missing_required_fields": report.missing_required_fields,
    }
