"""
corpus_manifest.py - Phase 2K reviewed corpus-candidate manifest tooling.

Builds a deterministic, sample-scope manifest from the Phase 2J accepted-ID
audit output plus the Phase 2H completed review CSV and Phase 2G filtering
metadata. This phase does not approve legal ground truth, QA generation,
fine-tuning, RAG indexing, or Phase 3 execution.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

PHASE_NAME = "Phase 2K - Reviewed Corpus Candidate Manifest"
MANIFEST_VERSION = "phase_2k_v1"
REVIEW_SCOPE = "phase_2h_sample_only"
APPROVAL_SCOPE = "later_corpus_candidate_review_only"

ACCEPTED_IDS_FILE = "accepted_candidate_ids_for_later_review.jsonl"
REVIEW_SAMPLE_FILE = "review_sample.jsonl"
COMPLETED_REVIEW_FILE = "reviewer_decisions_completed.csv"
FILTER_FILES = (
    "filtered_candidates.jsonl",
    "needs_review_candidates.jsonl",
    "rejected_candidates.jsonl",
)
FALSE_VALUES = {"false", "0", "no", "n"}
TRUE_VALUES = {"true", "1", "yes", "y"}


@dataclass
class ManifestMetrics:
    accepted_candidate_ids_input_count: int
    unique_accepted_candidate_ids_input_count: int
    duplicate_accepted_candidate_ids_count: int
    manifest_records_written: int
    missing_review_metadata_count: int
    missing_filter_metadata_count: int
    rejected_from_manifest_count: int
    unresolved_from_manifest_count: int
    unique_parent_documents: int
    unique_source_ids: int
    decision_counts: dict[str, int]
    confidence_counts: dict[str, int]
    legal_ground_truth_true_count: int
    rag_index_approved_true_count: int
    qa_generation_approved_true_count: int
    fine_tuning_approved_true_count: int
    phase3_ready_true_count: int
    counts_reconcile: bool
    manifest_verdict: str


@dataclass
class ManifestReport:
    phase: str
    manifest_version: str
    review_audit_dir: str
    review_pack_dir: str
    filter_dir: str
    output_dir: str
    status: str
    reason: str
    metrics: ManifestMetrics
    artifact_output_paths: dict[str, str] = field(default_factory=dict)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def is_true_value(value: Any) -> bool:
    return normalize_text(value).lower() in TRUE_VALUES


def stable_record_sort_key(record: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        normalize_text(record.get("candidate_id")),
        normalize_text(record.get("parent_record_id")),
        normalize_text(record.get("source_id")),
        normalize_text(record.get("review_sample_id")),
        normalize_text(record.get("filter_decision")),
    )


def review_row_sort_key(record: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    return (
        normalize_text(record.get("candidate_id")),
        normalize_text(record.get("review_date")),
        normalize_text(record.get("reviewer_id")),
        normalize_text(record.get("decision_label")),
        normalize_text(record.get("confidence")),
        normalize_text(record.get("review_sample_id")),
    )


def ordered_unique_candidate_ids(rows: list[dict[str, Any]]) -> tuple[list[str], int]:
    unique_ids: list[str] = []
    seen: set[str] = set()
    duplicates = 0
    for row in rows:
        candidate_id = normalize_text(row.get("candidate_id"))
        if not candidate_id:
            continue
        if candidate_id in seen:
            duplicates += 1
            continue
        seen.add(candidate_id)
        unique_ids.append(candidate_id)
    return unique_ids, duplicates


def index_by_candidate_id(
    rows: list[dict[str, Any]],
    *,
    sort_key,
) -> dict[str, list[dict[str, Any]]]:
    indexed: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        candidate_id = normalize_text(row.get("candidate_id"))
        if not candidate_id:
            continue
        indexed.setdefault(candidate_id, []).append(dict(row))
    for candidate_id, group in indexed.items():
        indexed[candidate_id] = sorted(group, key=sort_key)
    return indexed


def artifact_output_paths(output_dir: Path) -> dict[str, str]:
    return {
        "manifest_json": str((output_dir / "corpus_candidate_manifest.json").resolve()),
        "manifest_jsonl": str((output_dir / "corpus_candidate_manifest.jsonl").resolve()),
        "manifest_report_json": str((output_dir / "manifest_report.json").resolve()),
        "rejected_from_manifest_jsonl": str((output_dir / "rejected_from_manifest.jsonl").resolve()),
        "unresolved_from_manifest_jsonl": str((output_dir / "unresolved_from_manifest.jsonl").resolve()),
    }


def build_manifest_record(
    *,
    candidate_id: str,
    accepted_row: dict[str, Any],
    review_row: dict[str, Any],
    sample_row: dict[str, Any],
    filter_row: dict[str, Any],
) -> dict[str, Any]:
    record = {
        "candidate_id": candidate_id,
        "parent_record_id": normalize_text(sample_row.get("parent_record_id") or filter_row.get("parent_record_id")),
        "source_dataset": normalize_text(sample_row.get("source_dataset") or filter_row.get("source_dataset")),
        "source_id": normalize_text(sample_row.get("source_id") or filter_row.get("source_id")),
        "source_url": normalize_text(sample_row.get("source_url") or filter_row.get("source_url")),
        "license": normalize_text(sample_row.get("license") or filter_row.get("license")),
        "title": normalize_text(sample_row.get("title") or filter_row.get("title")),
        "article_number": sample_row.get("article_number", filter_row.get("article_number")),
        "article_title": normalize_text(sample_row.get("article_title") or filter_row.get("article_title")),
        "text_hash": normalize_text(
            sample_row.get("text_hash")
            or filter_row.get("text_hash")
            or filter_row.get("article_hash")
        ),
        "parser_version": normalize_text(sample_row.get("parser_version") or filter_row.get("parser_version")),
        "filter_version": normalize_text(sample_row.get("filter_version") or filter_row.get("filter_version")),
        "reviewer_id": normalize_text(review_row.get("reviewer_id")),
        "review_date": normalize_text(review_row.get("review_date")),
        "decision_label": normalize_text(review_row.get("decision_label")),
        "confidence": normalize_text(review_row.get("confidence")),
        "review_scope": REVIEW_SCOPE,
        "approval_scope": APPROVAL_SCOPE,
        "is_legal_ground_truth": False,
        "approved_for_rag_index": False,
        "approved_for_qa_generation": False,
        "approved_for_fine_tuning": False,
        "phase3_ready": False,
        "review_sample_id": normalize_text(sample_row.get("review_sample_id")),
        "sampling_bucket": normalize_text(sample_row.get("sampling_bucket")),
        "filter_decision": normalize_text(filter_row.get("filter_decision") or sample_row.get("filter_decision")),
        "accepted_audit_bucket": normalize_text(accepted_row.get("bucket")),
        "accepted_consensus_label": normalize_text(accepted_row.get("consensus_label")),
        "accepted_review_count": int(accepted_row.get("review_count") or 0),
    }
    return record


def validate_review_match(
    *,
    candidate_id: str,
    review_row: dict[str, Any] | None,
    sample_row: dict[str, Any] | None,
) -> list[str]:
    reasons: list[str] = []
    if review_row is None:
        reasons.append("missing_completed_review_row")
        return reasons
    if sample_row is None:
        reasons.append("missing_review_sample_row")
        return reasons
    if normalize_text(review_row.get("decision_label")) != "accept_for_later_corpus_candidate":
        reasons.append("review_decision_not_accept_for_later_corpus_candidate")
    if is_true_value(review_row.get("legal_ground_truth_approved")):
        reasons.append("review_row_legal_ground_truth_approved_true")
    if is_true_value(review_row.get("rag_index_approved")):
        reasons.append("review_row_rag_index_approved_true")
    if normalize_text(review_row.get("candidate_id")) != candidate_id:
        reasons.append("review_row_candidate_id_mismatch")
    if normalize_text(sample_row.get("candidate_id")) != candidate_id:
        reasons.append("review_sample_candidate_id_mismatch")
    return reasons


def filter_missing_fields(sample_row: dict[str, Any], filter_row: dict[str, Any]) -> list[str]:
    required_fields = (
        "candidate_id",
        "parent_record_id",
        "source_dataset",
        "license",
        "parser_version",
        "filter_version",
    )
    return [
        field
        for field in required_fields
        if not normalize_text(sample_row.get(field) or filter_row.get(field))
    ]


def manifest_report_to_dict(report: ManifestReport) -> dict[str, Any]:
    return {
        "phase": report.phase,
        "manifest_version": report.manifest_version,
        "review_audit_dir": report.review_audit_dir,
        "review_pack_dir": report.review_pack_dir,
        "filter_dir": report.filter_dir,
        "output_dir": report.output_dir,
        "status": report.status,
        "reason": report.reason,
        "metrics": asdict(report.metrics),
        "artifact_output_paths": report.artifact_output_paths,
    }


def build_corpus_candidate_manifest(
    *,
    review_audit_dir: Path,
    review_pack_dir: Path,
    filter_dir: Path,
    output_dir: Path,
) -> tuple[ManifestReport, dict[str, list[dict[str, Any]]]]:
    accepted_path = review_audit_dir / ACCEPTED_IDS_FILE
    review_sample_path = review_pack_dir / REVIEW_SAMPLE_FILE
    completed_review_path = review_pack_dir / COMPLETED_REVIEW_FILE

    missing_inputs = [
        str(path)
        for path in (accepted_path, review_sample_path, completed_review_path)
        if not path.exists()
    ]
    if missing_inputs:
        raise FileNotFoundError(
            "Missing required Phase 2K input files: " + ", ".join(missing_inputs)
        )

    missing_filter_inputs = [name for name in FILTER_FILES if not (filter_dir / name).exists()]
    if missing_filter_inputs:
        raise FileNotFoundError(
            "Missing required Phase 2G filter files: " + ", ".join(missing_filter_inputs)
        )

    accepted_rows = load_jsonl(accepted_path)
    review_sample_rows = load_jsonl(review_sample_path)
    completed_review_rows = load_csv(completed_review_path)
    filter_rows: list[dict[str, Any]] = []
    for name in FILTER_FILES:
        filter_rows.extend(load_jsonl(filter_dir / name))

    accepted_candidate_ids, duplicate_input_count = ordered_unique_candidate_ids(accepted_rows)
    sample_by_candidate = index_by_candidate_id(review_sample_rows, sort_key=stable_record_sort_key)
    review_by_candidate = index_by_candidate_id(completed_review_rows, sort_key=review_row_sort_key)
    filter_by_candidate = index_by_candidate_id(filter_rows, sort_key=stable_record_sort_key)

    manifest_records: list[dict[str, Any]] = []
    rejected_from_manifest: list[dict[str, Any]] = []
    unresolved_from_manifest: list[dict[str, Any]] = []

    for accepted_row in accepted_rows:
        candidate_id = normalize_text(accepted_row.get("candidate_id"))
        if not candidate_id:
            unresolved_from_manifest.append(
                {
                    "candidate_id": "",
                    "reason": "missing_candidate_id_in_accepted_ids_file",
                }
            )
            continue
        if candidate_id not in accepted_candidate_ids:
            continue

    for candidate_id in accepted_candidate_ids:
        accepted_match = next(
            row for row in accepted_rows if normalize_text(row.get("candidate_id")) == candidate_id
        )
        review_row = (review_by_candidate.get(candidate_id) or [None])[0]
        sample_row = (sample_by_candidate.get(candidate_id) or [None])[0]
        review_reasons = validate_review_match(
            candidate_id=candidate_id,
            review_row=review_row,
            sample_row=sample_row,
        )
        if review_reasons:
            rejected_from_manifest.append(
                {
                    "candidate_id": candidate_id,
                    "reasons": sorted(set(review_reasons)),
                }
            )
            continue

        filter_row = (filter_by_candidate.get(candidate_id) or [None])[0]
        if filter_row is None:
            unresolved_from_manifest.append(
                {
                    "candidate_id": candidate_id,
                    "reasons": ["missing_filter_metadata"],
                }
            )
            continue

        missing_filter_fields = filter_missing_fields(sample_row or {}, filter_row)
        if missing_filter_fields:
            unresolved_from_manifest.append(
                {
                    "candidate_id": candidate_id,
                    "reasons": ["missing_filter_metadata"],
                    "missing_fields": missing_filter_fields,
                }
            )
            continue

        manifest_records.append(
            build_manifest_record(
                candidate_id=candidate_id,
                accepted_row=accepted_match,
                review_row=review_row or {},
                sample_row=sample_row or {},
                filter_row=filter_row,
            )
        )

    manifest_records.sort(key=lambda item: normalize_text(item.get("candidate_id")))
    decision_counts = dict(
        sorted(Counter(normalize_text(item.get("decision_label")) for item in manifest_records).items())
    )
    confidence_counts = dict(
        sorted(Counter(normalize_text(item.get("confidence")) for item in manifest_records).items())
    )
    ground_truth_true = sum(1 for item in manifest_records if bool(item.get("is_legal_ground_truth")) is True)
    rag_true = sum(1 for item in manifest_records if bool(item.get("approved_for_rag_index")) is True)
    qa_true = sum(1 for item in manifest_records if bool(item.get("approved_for_qa_generation")) is True)
    fine_tuning_true = sum(1 for item in manifest_records if bool(item.get("approved_for_fine_tuning")) is True)
    phase3_ready_true = sum(1 for item in manifest_records if bool(item.get("phase3_ready")) is True)
    counts_reconcile = len(accepted_candidate_ids) == (
        len(manifest_records) + len(rejected_from_manifest) + len(unresolved_from_manifest)
    )

    if not counts_reconcile or rejected_from_manifest or ground_truth_true or rag_true or qa_true or fine_tuning_true or phase3_ready_true:
        verdict = "FAIL"
        reason = "Manifest build failed closed because review metadata or safety constraints did not reconcile."
    else:
        verdict = "PASS WITH RISKS"
        reason = "Sample-scope corpus candidate manifest built successfully, but downstream approval remains blocked."

    metrics = ManifestMetrics(
        accepted_candidate_ids_input_count=len(accepted_rows),
        unique_accepted_candidate_ids_input_count=len(accepted_candidate_ids),
        duplicate_accepted_candidate_ids_count=duplicate_input_count,
        manifest_records_written=len(manifest_records),
        missing_review_metadata_count=len(rejected_from_manifest),
        missing_filter_metadata_count=sum(
            1 for item in unresolved_from_manifest if "missing_filter_metadata" in item.get("reasons", [])
        ),
        rejected_from_manifest_count=len(rejected_from_manifest),
        unresolved_from_manifest_count=len(unresolved_from_manifest),
        unique_parent_documents=len(
            {
                normalize_text(item.get("parent_record_id"))
                for item in manifest_records
                if normalize_text(item.get("parent_record_id"))
            }
        ),
        unique_source_ids=len(
            {
                normalize_text(item.get("source_id"))
                for item in manifest_records
                if normalize_text(item.get("source_id"))
            }
        ),
        decision_counts=decision_counts,
        confidence_counts=confidence_counts,
        legal_ground_truth_true_count=ground_truth_true,
        rag_index_approved_true_count=rag_true,
        qa_generation_approved_true_count=qa_true,
        fine_tuning_approved_true_count=fine_tuning_true,
        phase3_ready_true_count=phase3_ready_true,
        counts_reconcile=counts_reconcile,
        manifest_verdict=verdict,
    )
    report = ManifestReport(
        phase=PHASE_NAME,
        manifest_version=MANIFEST_VERSION,
        review_audit_dir=str(review_audit_dir.resolve()),
        review_pack_dir=str(review_pack_dir.resolve()),
        filter_dir=str(filter_dir.resolve()),
        output_dir=str(output_dir.resolve()),
        status=verdict,
        reason=reason,
        metrics=metrics,
        artifact_output_paths=artifact_output_paths(output_dir),
    )

    write_json(output_dir / "manifest_report.json", manifest_report_to_dict(report))
    if rejected_from_manifest:
        write_jsonl(output_dir / "rejected_from_manifest.jsonl", rejected_from_manifest)
    if unresolved_from_manifest:
        write_jsonl(output_dir / "unresolved_from_manifest.jsonl", unresolved_from_manifest)

    if verdict != "FAIL":
        write_json(output_dir / "corpus_candidate_manifest.json", {"records": manifest_records})
        write_jsonl(output_dir / "corpus_candidate_manifest.jsonl", manifest_records)

    return report, {
        "manifest_records": manifest_records,
        "rejected_from_manifest": rejected_from_manifest,
        "unresolved_from_manifest": unresolved_from_manifest,
    }
