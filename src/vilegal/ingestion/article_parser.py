"""
article_parser.py - Phase 2F deterministic secondary parser for UTS_VLC.

Parses existing document-level normalized records into article/chunk candidates
for analysis only. This module does not verify legal correctness, does not
generate QA, and does not build any retrieval index.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

PARSER_VERSION = "phase_2f_v1"
NEAR_EMPTY_CHAR_THRESHOLD = 50
SUSPICIOUS_ARTICLE_MIN_CHARS = 100
SUSPICIOUS_ARTICLE_MAX_CHARS = 50000
MAX_CHUNK_CHARS = 4000

ARTICLE_LABEL_PATTERN = r"(?:Điều|Dieu|Äiá»u|ÄIá»€U|Ðiá»u|ĐIỀU)"
ARTICLE_LINE_RE = re.compile(
    rf"(?m)^(?P<prefix>\s{{0,3}}(?:#{{1,6}}\s*)?)"
    rf"(?P<label>{ARTICLE_LABEL_PATTERN})\s+"
    rf"(?P<number>\d+)"
    rf"(?P<separator>[ \t]*(?:[.:]|-)?[ \t]*)"
    rf"(?P<title>[^\n]*)$"
)

REQUIRED_PARENT_PROVENANCE = (
    "source_dataset",
    "license",
    "retrieved_at",
    "record_id",
)


@dataclass(frozen=True)
class ArticleMarker:
    start: int
    end: int
    article_number: int | None
    article_title: str | None
    marker_text: str
    is_markdown_heading: bool
    flags: tuple[str, ...] = ()


@dataclass
class ParseWarning:
    parent_record_id: str
    source_id: str
    code: str
    message: str


@dataclass
class RejectedDocument:
    parent_record_id: str
    source_id: str
    reason: str
    missing_fields: list[str] = field(default_factory=list)


@dataclass
class ParseMetrics:
    input_document_count: int
    documents_with_article_markers: int
    documents_without_article_markers: int
    derived_article_count: int
    empty_derived_article_count: int
    near_empty_derived_article_count: int
    duplicate_article_hash_count: int
    documents_with_single_article: int
    documents_with_multiple_articles: int
    article_number_parse_success_rate: float
    parent_provenance_coverage: float
    suspicious_article_length_count: int
    parse_warning_count: int


@dataclass
class ParseReport:
    phase: str
    parser_version: str
    input_dir: str
    output_dir: str
    status: str
    blocked: bool
    reason: str
    metrics: ParseMetrics
    safety_gates: dict[str, Any]
    warnings_summary: dict[str, int]
    blocked_missing_provenance_fields: list[str] = field(default_factory=list)


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


def stripped_len(value: Any) -> int:
    if value is None:
        return 0
    return len(str(value).strip())


def is_blank(value: Any) -> bool:
    return stripped_len(value) == 0


def text_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]


def detect_article_markers(text: str) -> list[ArticleMarker]:
    markers: list[ArticleMarker] = []
    for match in ARTICLE_LINE_RE.finditer(text):
        number_text = match.group("number")
        article_number = int(number_text) if number_text.isdigit() else None
        title = match.group("title").strip() or None
        if title is not None and all(char in ".:-" for char in title):
            title = None
        prefix = match.group("prefix") or ""
        flags: list[str] = []
        if prefix.strip().startswith("#"):
            flags.append("markdown_heading_marker")
        if title is None:
            flags.append("article_title_missing")
        markers.append(
            ArticleMarker(
                start=match.start(),
                end=match.end(),
                article_number=article_number,
                article_title=title,
                marker_text=match.group(0),
                is_markdown_heading=prefix.strip().startswith("#"),
                flags=tuple(flags),
            )
        )
    return markers


def chunk_article_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    content = text.strip()
    if not content:
        return [""]
    if len(content) <= max_chars:
        return [content]

    chunks: list[str] = []
    current = ""
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", content) if part.strip()]
    for paragraph in paragraphs:
        candidate = paragraph if not current else current + "\n\n" + paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = ""
        if len(paragraph) <= max_chars:
            current = paragraph
            continue
        lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        line_buffer = ""
        for line in lines:
            line_candidate = line if not line_buffer else line_buffer + "\n" + line
            if len(line_candidate) <= max_chars:
                line_buffer = line_candidate
            else:
                if line_buffer:
                    chunks.append(line_buffer)
                line_buffer = line
        if line_buffer:
            current = line_buffer

    if current:
        chunks.append(current)
    return chunks or [content]


def split_document_into_articles(text: str) -> tuple[list[dict[str, Any]], list[ParseWarning]]:
    markers = detect_article_markers(text)
    warnings: list[ParseWarning] = []
    if not markers:
        return [], warnings

    articles: list[dict[str, Any]] = []
    preamble = text[:markers[0].start].strip()
    if preamble:
        warnings.append(
            ParseWarning(
                parent_record_id="",
                source_id="",
                code="preamble_before_first_article",
                message="Document contains non-empty preamble before the first article marker.",
            )
        )

    for index, marker in enumerate(markers):
        next_start = markers[index + 1].start if index + 1 < len(markers) else len(text)
        article_text = text[marker.start:next_start].strip()
        flags = list(marker.flags)
        if stripped_len(article_text) < SUSPICIOUS_ARTICLE_MIN_CHARS:
            flags.append("suspicious_short_article")
        if stripped_len(article_text) > SUSPICIOUS_ARTICLE_MAX_CHARS:
            flags.append("suspicious_long_article")
        articles.append(
            {
                "article_number": marker.article_number,
                "article_title": marker.article_title,
                "text": article_text,
                "parse_flags": sorted(set(flags)),
                "is_markdown_heading": marker.is_markdown_heading,
            }
        )
    return articles, warnings


def validate_parent_provenance(record: dict[str, Any]) -> list[str]:
    missing = [field for field in REQUIRED_PARENT_PROVENANCE if is_blank(record.get(field))]
    if is_blank(record.get("source_id")) and is_blank(record.get("source_url")):
        missing.append("source_id_or_source_url")
    return missing


def derive_candidates_from_document(record: dict[str, Any]) -> tuple[list[dict[str, Any]], list[ParseWarning], RejectedDocument | None]:
    missing_fields = validate_parent_provenance(record)
    if missing_fields:
        return [], [], RejectedDocument(
            parent_record_id=str(record.get("record_id") or ""),
            source_id=str(record.get("source_id") or ""),
            reason="missing_required_provenance",
            missing_fields=missing_fields,
        )

    text = str(record.get("text") or "").strip()
    if not text:
        return [], [], RejectedDocument(
            parent_record_id=str(record.get("record_id") or ""),
            source_id=str(record.get("source_id") or ""),
            reason="blank_document_text",
        )

    articles, warnings = split_document_into_articles(text)
    if not articles:
        return [], warnings, RejectedDocument(
            parent_record_id=str(record.get("record_id") or ""),
            source_id=str(record.get("source_id") or ""),
            reason="no_article_markers_detected",
        )

    parent_record_id = str(record["record_id"])
    source_id = str(record.get("source_id") or "")
    parent_title = str(record.get("title") or "")
    for warning in warnings:
        warning.parent_record_id = parent_record_id
        warning.source_id = source_id

    candidates: list[dict[str, Any]] = []
    for article in articles:
        chunks = chunk_article_text(article["text"])
        for chunk_index, chunk_text in enumerate(chunks):
            parse_flags = list(article["parse_flags"])
            if len(chunks) > 1:
                parse_flags.append("split_into_multiple_chunks")
            if article["article_number"] is None:
                parse_flags.append("article_number_unparsed")
            if not article["article_title"]:
                parse_flags.append("article_title_missing")
            candidate = {
                "parent_record_id": parent_record_id,
                "source_dataset": record["source_dataset"],
                "source_id": record.get("source_id"),
                "source_url": record.get("source_url"),
                "license": record["license"],
                "retrieved_at": record["retrieved_at"],
                "title": parent_title,
                "parent_document_type": record.get("document_type"),
                "parent_document_number": record.get("document_number"),
                "article_number": article["article_number"],
                "article_title": article["article_title"],
                "chunk_index": chunk_index,
                "text": chunk_text.strip(),
                "text_hash": text_hash(chunk_text),
                "parser_version": PARSER_VERSION,
                "parse_flags": sorted(set(parse_flags)),
                "uncertain_parse": bool(parse_flags),
                "is_legal_ground_truth": False,
                "approved_for_rag_index": False,
            }
            candidates.append(candidate)

    return candidates, warnings, None


def duplicate_hash_count(candidates: list[dict[str, Any]]) -> int:
    seen: set[str] = set()
    duplicate_count = 0
    for candidate in candidates:
        digest = str(candidate.get("text_hash") or "")
        if digest in seen:
            duplicate_count += 1
        seen.add(digest)
    return duplicate_count


def warnings_summary(warnings: list[ParseWarning]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for warning in warnings:
        summary[warning.code] = summary.get(warning.code, 0) + 1
    return dict(sorted(summary.items()))


def build_metrics(
    input_document_count: int,
    marker_counts: list[int],
    candidates: list[dict[str, Any]],
    warnings: list[ParseWarning],
    provenance_failures: int,
) -> ParseMetrics:
    derived_count = len(candidates)
    empty_count = sum(1 for item in candidates if stripped_len(item.get("text")) == 0)
    near_empty_count = sum(
        1 for item in candidates if stripped_len(item.get("text")) <= NEAR_EMPTY_CHAR_THRESHOLD
    )
    suspicious_count = sum(
        1
        for item in candidates
        if stripped_len(item.get("text")) < SUSPICIOUS_ARTICLE_MIN_CHARS
        or stripped_len(item.get("text")) > SUSPICIOUS_ARTICLE_MAX_CHARS
    )
    parse_success_count = sum(1 for item in candidates if item.get("article_number") is not None)
    docs_with_markers = sum(1 for count in marker_counts if count > 0)
    docs_without_markers = sum(1 for count in marker_counts if count == 0)
    single_article_docs = sum(1 for count in marker_counts if count == 1)
    multi_article_docs = sum(1 for count in marker_counts if count > 1)
    coverage = 0.0 if input_document_count == 0 else round(
        (input_document_count - provenance_failures) / input_document_count,
        6,
    )
    rate = 0.0 if derived_count == 0 else round(parse_success_count / derived_count, 6)
    return ParseMetrics(
        input_document_count=input_document_count,
        documents_with_article_markers=docs_with_markers,
        documents_without_article_markers=docs_without_markers,
        derived_article_count=derived_count,
        empty_derived_article_count=empty_count,
        near_empty_derived_article_count=near_empty_count,
        duplicate_article_hash_count=duplicate_hash_count(candidates),
        documents_with_single_article=single_article_docs,
        documents_with_multiple_articles=multi_article_docs,
        article_number_parse_success_rate=rate,
        parent_provenance_coverage=coverage,
        suspicious_article_length_count=suspicious_count,
        parse_warning_count=len(warnings),
    )


def build_parse_report(
    *,
    input_dir: Path,
    output_dir: Path,
    status: str,
    blocked: bool,
    reason: str,
    metrics: ParseMetrics,
    warnings: list[ParseWarning],
    blocked_missing_fields: list[str] | None = None,
) -> ParseReport:
    empty_rate = 0.0 if metrics.derived_article_count == 0 else round(
        metrics.empty_derived_article_count / metrics.derived_article_count, 6
    )
    gates = {
        "empty_derived_article_rate_lte_0_5_percent": empty_rate <= 0.005,
        "parent_provenance_coverage_is_100_percent": metrics.parent_provenance_coverage == 1.0,
        "all_candidates_marked_not_ground_truth": True,
        "all_candidates_marked_not_approved_for_rag_index": True,
    }
    return ParseReport(
        phase="Phase 2F - UTS_VLC Article/Chunk Parser Design and Validation",
        parser_version=PARSER_VERSION,
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        status=status,
        blocked=blocked,
        reason=reason,
        metrics=metrics,
        safety_gates=gates,
        warnings_summary=warnings_summary(warnings),
        blocked_missing_provenance_fields=sorted(set(blocked_missing_fields or [])),
    )


def parse_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[RejectedDocument], list[ParseWarning], ParseMetrics]:
    all_candidates: list[dict[str, Any]] = []
    rejected: list[RejectedDocument] = []
    warnings: list[ParseWarning] = []
    marker_counts: list[int] = []
    provenance_failures = 0

    for record in records:
        missing = validate_parent_provenance(record)
        if missing:
            provenance_failures += 1
            marker_counts.append(0)
            rejected.append(
                RejectedDocument(
                    parent_record_id=str(record.get("record_id") or ""),
                    source_id=str(record.get("source_id") or ""),
                    reason="missing_required_provenance",
                    missing_fields=missing,
                )
            )
            continue

        markers = detect_article_markers(str(record.get("text") or ""))
        marker_counts.append(len(markers))
        candidates, doc_warnings, rejected_doc = derive_candidates_from_document(record)
        all_candidates.extend(candidates)
        warnings.extend(doc_warnings)
        if rejected_doc is not None:
            rejected.append(rejected_doc)

    metrics = build_metrics(
        input_document_count=len(records),
        marker_counts=marker_counts,
        candidates=all_candidates,
        warnings=warnings,
        provenance_failures=provenance_failures,
    )
    return all_candidates, rejected, warnings, metrics


def serialize_warning(warning: ParseWarning) -> dict[str, Any]:
    return asdict(warning)


def serialize_rejected(rejected: RejectedDocument) -> dict[str, Any]:
    return asdict(rejected)
