"""
review_sampler.py - Phase 2H deterministic manual-review sampling for Phase 2G outputs.

Builds a review-only sampling pack from existing Phase 2G filtering artifacts.
This module never promotes candidates to legal ground truth and never approves
them for RAG indexing.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DEFAULT_SAMPLE_SIZE = 150
DEFAULT_SEED = 42
REVIEW_SAMPLER_VERSION = "phase_2h_v1"

BUCKET_ORDER = (
    "duplicate_related",
    "suspicious_length",
    "keep_candidate_for_human_review",
    "needs_review",
    "rejected",
)

BASE_BUCKET_TARGETS = {
    "keep_candidate_for_human_review": 60,
    "needs_review": 50,
    "rejected": 20,
    "duplicate_related": 10,
    "suspicious_length": 10,
}

REQUIRED_INPUT_FILES = (
    "filtered_candidates.jsonl",
    "rejected_candidates.jsonl",
    "needs_review_candidates.jsonl",
    "filter_report.json",
)

REQUIRED_REVIEW_FIELDS = (
    "review_sample_id",
    "candidate_id",
    "parent_record_id",
    "source_dataset",
    "source_id",
    "source_url",
    "license",
    "title",
    "article_number",
    "article_title",
    "filter_decision",
    "filter_reasons",
    "risk_flags",
    "text_length",
    "text_hash",
    "parser_version",
    "filter_version",
    "sampling_seed",
    "sampling_bucket",
    "is_legal_ground_truth",
    "approved_for_rag_index",
)

REVIEWER_TEMPLATE_FIELDS = (
    "review_sample_id",
    "candidate_id",
    "parent_record_id",
    "source_dataset",
    "source_id",
    "source_url",
    "license",
    "title",
    "article_number",
    "article_title",
    "filter_decision",
    "sampling_bucket",
    "reviewer_id",
    "review_date",
    "decision_label",
    "confidence",
    "notes",
    "legal_ground_truth_approved",
    "rag_index_approved",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def row_key(record: dict[str, Any]) -> str:
    return str(record.get("input_index") if record.get("input_index") is not None else record.get("candidate_id") or "")


def unique_row_keys(records: list[dict[str, Any]]) -> set[str]:
    return {row_key(record) for record in records}


def is_rejected(record: dict[str, Any]) -> bool:
    return str(record.get("filter_decision") or "").startswith("reject_")


def is_needs_review(record: dict[str, Any]) -> bool:
    return str(record.get("filter_decision") or "").startswith("needs_review_")


def is_keep(record: dict[str, Any]) -> bool:
    return str(record.get("filter_decision") or "") == "keep_candidate_for_human_review"


def has_parent_warning(record: dict[str, Any]) -> bool:
    return bool(record.get("parent_document_warning_codes"))


def is_duplicate_related(record: dict[str, Any], duplicate_group_sizes: dict[str, int]) -> bool:
    article_hash = str(record.get("article_hash") or "")
    return (
        "reject_duplicate_hash" in (record.get("filter_reasons") or [])
        or "duplicate_hash_loser" in (record.get("risk_flags") or [])
        or bool(record.get("duplicate_of"))
        or duplicate_group_sizes.get(article_hash, 0) > 1
    )


def is_suspicious_length(record: dict[str, Any]) -> bool:
    return (
        "needs_review_suspicious_length" in (record.get("filter_reasons") or [])
        or "suspicious_length_text" in (record.get("risk_flags") or [])
    )


def stable_digest(seed: int, bucket: str, value: str) -> str:
    return hashlib.sha256(f"{seed}|{bucket}|{value}".encode("utf-8")).hexdigest()


def parent_rank(seed: int, bucket: str, parent_record_id: str) -> str:
    return stable_digest(seed, f"{bucket}:parent", parent_record_id)


def record_rank(record: dict[str, Any], seed: int, bucket: str) -> str:
    return stable_digest(
        seed,
        bucket,
        "|".join(
            [
                row_key(record),
                str(record.get("candidate_id") or ""),
                str(record.get("parent_record_id") or ""),
                str(record.get("article_hash") or ""),
            ]
        ),
    )


def round_robin_order(
    records: list[dict[str, Any]],
    *,
    seed: int,
    bucket: str,
    prioritize_parent_warning: bool = False,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        parent_id = str(record.get("parent_record_id") or "")
        grouped[parent_id].append(record)

    ordered_groups: dict[str, list[dict[str, Any]]] = {}
    for parent_id, items in grouped.items():
        ordered_groups[parent_id] = sorted(
            items,
            key=lambda item: (
                0 if prioritize_parent_warning and has_parent_warning(item) else 1,
                record_rank(item, seed, bucket),
                row_key(item),
            ),
        )

    parent_order = sorted(
        ordered_groups.keys(),
        key=lambda parent_id: (parent_rank(seed, bucket, parent_id), parent_id),
    )

    pending = {parent_id: list(items) for parent_id, items in ordered_groups.items()}
    ordered: list[dict[str, Any]] = []
    active_parents = list(parent_order)
    while active_parents:
        next_active: list[str] = []
        for parent_id in active_parents:
            items = pending.get(parent_id, [])
            if not items:
                continue
            ordered.append(items.pop(0))
            if items:
                pending[parent_id] = items
                next_active.append(parent_id)
            else:
                pending.pop(parent_id, None)
        active_parents = next_active
    return ordered


def select_records(
    pool: list[dict[str, Any]],
    *,
    target: int,
    seed: int,
    bucket: str,
    excluded_row_keys: set[str],
    prioritize_parent_warning: bool = False,
) -> tuple[list[dict[str, Any]], int]:
    available_records = [record for record in pool if row_key(record) not in excluded_row_keys]
    ordered = round_robin_order(
        available_records,
        seed=seed,
        bucket=bucket,
        prioritize_parent_warning=prioritize_parent_warning,
    )
    selected = ordered[:target]
    shortfall = max(target - len(selected), 0)
    return selected, shortfall


def scale_bucket_targets(sample_size: int) -> dict[str, int]:
    total_weight = sum(BASE_BUCKET_TARGETS.values())
    scaled: dict[str, int] = {}
    remainders: list[tuple[float, str]] = []
    allocated = 0
    for bucket in BUCKET_ORDER:
        raw = (BASE_BUCKET_TARGETS[bucket] / total_weight) * sample_size
        count = math.floor(raw)
        scaled[bucket] = count
        allocated += count
        remainders.append((raw - count, bucket))

    for _, bucket in sorted(remainders, key=lambda item: (-item[0], BUCKET_ORDER.index(item[1]))):
        if allocated >= sample_size:
            break
        scaled[bucket] += 1
        allocated += 1
    return scaled


def build_duplicate_group_pool(
    records: list[dict[str, Any]],
    duplicate_group_sizes: dict[str, int],
    *,
    seed: int,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        article_hash = str(record.get("article_hash") or "")
        if article_hash and duplicate_group_sizes.get(article_hash, 0) > 1:
            grouped[article_hash].append(record)

    representatives: list[dict[str, Any]] = []
    for article_hash, items in sorted(grouped.items()):
        ordered = sorted(
            items,
            key=lambda item: (
                0 if str(item.get("filter_decision") or "") == "reject_duplicate_hash" else 1,
                0 if has_parent_warning(item) else 1,
                record_rank(item, seed, "duplicate_related_group"),
                row_key(item),
            ),
        )
        representative = dict(ordered[0])
        representative["duplicate_group_size"] = int(duplicate_group_sizes.get(article_hash, len(items)))
        representative["duplicate_group_key"] = article_hash
        representatives.append(representative)
    return representatives


def normalize_review_record(
    record: dict[str, Any],
    *,
    sampling_bucket: str,
    sampling_seed: int,
    sample_index: int,
    filter_version: str,
) -> dict[str, Any]:
    normalized = dict(record)
    normalized["review_sample_id"] = (
        f"phase2h-{sampling_bucket}-{sample_index:03d}-"
        f"{stable_digest(sampling_seed, sampling_bucket, row_key(record))[:12]}"
    )
    normalized["text_length"] = int(record.get("text_char_count") or len(str(record.get("text") or "").strip()))
    normalized["text_hash"] = str(record.get("article_hash") or record.get("text_hash") or "")
    normalized["filter_version"] = filter_version
    normalized["sampling_seed"] = sampling_seed
    normalized["sampling_bucket"] = sampling_bucket
    normalized["approved_for_rag_index"] = False
    normalized["is_legal_ground_truth"] = False
    normalized.setdefault("source_id", "")
    normalized.setdefault("source_url", "")
    normalized.setdefault("article_number", None)
    normalized.setdefault("article_title", "")
    normalized.setdefault("title", "")
    return normalized


def required_review_fields_present(record: dict[str, Any]) -> bool:
    return all(field in record for field in REQUIRED_REVIEW_FIELDS)


def report_output_paths(output_dir: Path) -> dict[str, str]:
    return {
        "review_sample_jsonl": str((output_dir / "review_sample.jsonl").resolve()),
        "review_sample_csv": str((output_dir / "review_sample.csv").resolve()),
        "review_manifest_json": str((output_dir / "review_manifest.json").resolve()),
        "sampling_report_json": str((output_dir / "sampling_report.json").resolve()),
        "duplicate_group_sample_jsonl": str((output_dir / "duplicate_group_sample.jsonl").resolve()),
        "suspicious_length_sample_jsonl": str((output_dir / "suspicious_length_sample.jsonl").resolve()),
        "keep_sample_jsonl": str((output_dir / "keep_sample.jsonl").resolve()),
        "needs_review_sample_jsonl": str((output_dir / "needs_review_sample.jsonl").resolve()),
        "rejected_sample_jsonl": str((output_dir / "rejected_sample.jsonl").resolve()),
        "reviewer_decision_template_csv": str((output_dir / "reviewer_decision_template.csv").resolve()),
    }


def dynamic_csv_fieldnames(records: list[dict[str, Any]], required: tuple[str, ...]) -> list[str]:
    seen = set(required)
    extras: set[str] = set()
    for record in records:
        extras.update(record.keys())
    ordered_extras = sorted(field for field in extras if field not in seen)
    return [*required, *ordered_extras]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def review_template_rows(sample_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in sample_records:
        rows.append(
            {
                "review_sample_id": record.get("review_sample_id"),
                "candidate_id": record.get("candidate_id"),
                "parent_record_id": record.get("parent_record_id"),
                "source_dataset": record.get("source_dataset"),
                "source_id": record.get("source_id"),
                "source_url": record.get("source_url"),
                "license": record.get("license"),
                "title": record.get("title"),
                "article_number": record.get("article_number"),
                "article_title": record.get("article_title"),
                "filter_decision": record.get("filter_decision"),
                "sampling_bucket": record.get("sampling_bucket"),
                "reviewer_id": "",
                "review_date": "",
                "decision_label": "",
                "confidence": "",
                "notes": "",
                "legal_ground_truth_approved": False,
                "rag_index_approved": False,
            }
        )
    return rows


def validate_phase2g_inputs(input_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    missing = [name for name in REQUIRED_INPUT_FILES if not (input_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing required Phase 2G files: {missing}")

    filtered = load_jsonl(input_dir / "filtered_candidates.jsonl")
    rejected = load_jsonl(input_dir / "rejected_candidates.jsonl")
    needs_review = load_jsonl(input_dir / "needs_review_candidates.jsonl")
    filter_report = load_json(input_dir / "filter_report.json")

    filtered_row_keys = unique_row_keys(filtered)
    rejected_row_keys = unique_row_keys(rejected)
    needs_review_row_keys = unique_row_keys(needs_review)
    missing_subset_keys = (rejected_row_keys | needs_review_row_keys) - filtered_row_keys
    if missing_subset_keys:
        raise ValueError("Phase 2G subset outputs contain rows not present in filtered_candidates.jsonl.")

    metrics = filter_report.get("metrics") or {}
    expected_total = int(metrics.get("total_input_candidates") or len(filtered))
    expected_rejected = int(metrics.get("total_rejected") or len(rejected))
    expected_needs_review = int(metrics.get("total_needs_review") or len(needs_review))
    if len(filtered) != expected_total:
        raise ValueError("filtered_candidates.jsonl count does not match filter_report.json.")
    if len(rejected) != expected_rejected:
        raise ValueError("rejected_candidates.jsonl count does not match filter_report.json.")
    if len(needs_review) != expected_needs_review:
        raise ValueError("needs_review_candidates.jsonl count does not match filter_report.json.")
    return filtered, filter_report


def build_review_pack(
    *,
    input_dir: Path,
    output_dir: Path,
    sample_size: int,
    seed: int,
    rubric_path: Path | None = None,
) -> dict[str, Any]:
    filtered_records, filter_report = validate_phase2g_inputs(input_dir)
    duplicate_group_sizes = {
        str(key): int(value)
        for key, value in (filter_report.get("duplicate_group_sizes") or {}).items()
    }
    filter_version = str(filter_report.get("filter_version") or "")

    if sample_size <= 0:
        raise ValueError("sample_size must be positive.")

    bucket_targets = scale_bucket_targets(sample_size)
    excluded_row_keys: set[str] = set()
    bucket_shortfalls: dict[str, int] = {}

    duplicate_pool = build_duplicate_group_pool(filtered_records, duplicate_group_sizes, seed=seed)
    suspicious_pool = [record for record in filtered_records if is_suspicious_length(record)]
    keep_pool = [record for record in filtered_records if is_keep(record)]
    needs_review_pool = [record for record in filtered_records if is_needs_review(record)]
    rejected_pool = [record for record in filtered_records if is_rejected(record)]

    selected_by_bucket_raw: dict[str, list[dict[str, Any]]] = {}
    sampling_pools = {
        "duplicate_related": duplicate_pool,
        "suspicious_length": suspicious_pool,
        "keep_candidate_for_human_review": keep_pool,
        "needs_review": needs_review_pool,
        "rejected": rejected_pool,
    }

    for bucket in BUCKET_ORDER:
        selected, shortfall = select_records(
            sampling_pools[bucket],
            target=bucket_targets[bucket],
            seed=seed,
            bucket=bucket,
            excluded_row_keys=excluded_row_keys,
            prioritize_parent_warning=True,
        )
        selected_by_bucket_raw[bucket] = selected
        bucket_shortfalls[bucket] = shortfall
        excluded_row_keys.update(row_key(record) for record in selected)

    review_sample: list[dict[str, Any]] = []
    selected_by_bucket: dict[str, list[dict[str, Any]]] = {}
    sample_index = 1
    for bucket in BUCKET_ORDER:
        normalized_records: list[dict[str, Any]] = []
        for record in selected_by_bucket_raw[bucket]:
            normalized = normalize_review_record(
                record,
                sampling_bucket=bucket,
                sampling_seed=seed,
                sample_index=sample_index,
                filter_version=filter_version,
            )
            normalized_records.append(normalized)
            review_sample.append(normalized)
            sample_index += 1
        selected_by_bucket[bucket] = normalized_records

    sampled_by_bucket = {bucket: len(records) for bucket, records in selected_by_bucket.items()}
    sampled_by_filter_decision = dict(sorted(Counter(str(record.get("filter_decision") or "") for record in review_sample).items()))
    sampled_parent_warning_examples = sum(1 for record in review_sample if has_parent_warning(record))
    approved_true = sum(1 for record in review_sample if bool(record.get("approved_for_rag_index")) is True)
    ground_truth_true = sum(1 for record in review_sample if bool(record.get("is_legal_ground_truth")) is True)
    total_sampled = len(review_sample)
    parent_documents_covered = len({str(record.get("parent_record_id") or "") for record in review_sample if record.get("parent_record_id")})
    sources_covered = {
        "source_datasets": sorted({str(record.get("source_dataset") or "") for record in review_sample if record.get("source_dataset")}),
        "source_id_count": len({str(record.get("source_id") or "") for record in review_sample if record.get("source_id")}),
        "licenses": sorted({str(record.get("license") or "") for record in review_sample if record.get("license")}),
    }

    counts_reconcile = total_sampled == sum(sampled_by_bucket.values())
    required_fields_ok = all(required_review_fields_present(record) for record in review_sample)
    rubric_exists = rubric_path.exists() if rubric_path is not None else True
    shortfalls_reported = all(
        bucket in bucket_shortfalls and bucket_shortfalls[bucket] >= 0
        for bucket in BUCKET_ORDER
    )

    if not counts_reconcile or not required_fields_ok or approved_true > 0 or ground_truth_true > 0 or not rubric_exists or not shortfalls_reported:
        safety_verdict = "FAIL"
    elif any(bucket_shortfalls.values()) or sampled_parent_warning_examples > 0 or sampled_by_filter_decision:
        safety_verdict = "PASS WITH RISKS"
    else:
        safety_verdict = "PASS"

    output_paths = report_output_paths(output_dir)
    manifest = {
        "phase": "Phase 2H - Manual Review Pack / Sampling Audit",
        "review_sampler_version": REVIEW_SAMPLER_VERSION,
        "filter_version": filter_version,
        "input_dir": str(input_dir.resolve()),
        "output_dir": str(output_dir.resolve()),
        "source_manifest_path": str(filter_report.get("source_manifest_path") or ""),
        "sample_size_requested": sample_size,
        "sample_size_actual": total_sampled,
        "sampling_seed": seed,
        "bucket_targets": bucket_targets,
        "bucket_shortfalls": bucket_shortfalls,
        "artifact_output_paths": output_paths,
    }
    sampling_report = {
        "phase": "Phase 2H - Manual Review Pack / Sampling Audit",
        "status": safety_verdict,
        "total_available_candidates": len(filtered_records),
        "total_sampled": total_sampled,
        "sampled_by_bucket": sampled_by_bucket,
        "sampled_by_filter_decision": sampled_by_filter_decision,
        "sampled_duplicate_examples": sampled_by_bucket.get("duplicate_related", 0),
        "sampled_suspicious_length_examples": sampled_by_bucket.get("suspicious_length", 0),
        "sampled_parent_warning_examples": sampled_parent_warning_examples,
        "sources_covered": sources_covered,
        "parent_documents_covered": parent_documents_covered,
        "sampling_seed": seed,
        "sample_size_requested": sample_size,
        "sample_size_actual": total_sampled,
        "bucket_targets": bucket_targets,
        "bucket_shortfalls": bucket_shortfalls,
        "approved_for_rag_index_true_count": approved_true,
        "is_legal_ground_truth_true_count": ground_truth_true,
        "artifact_output_paths": output_paths,
        "safety_verdict": safety_verdict,
    }

    write_jsonl(output_dir / "review_sample.jsonl", review_sample)
    write_jsonl(output_dir / "duplicate_group_sample.jsonl", selected_by_bucket["duplicate_related"])
    write_jsonl(output_dir / "suspicious_length_sample.jsonl", selected_by_bucket["suspicious_length"])
    write_jsonl(output_dir / "keep_sample.jsonl", selected_by_bucket["keep_candidate_for_human_review"])
    write_jsonl(output_dir / "needs_review_sample.jsonl", selected_by_bucket["needs_review"])
    write_jsonl(output_dir / "rejected_sample.jsonl", selected_by_bucket["rejected"])
    write_json(output_dir / "review_manifest.json", manifest)
    write_json(output_dir / "sampling_report.json", sampling_report)
    write_csv(
        output_dir / "review_sample.csv",
        review_sample,
        dynamic_csv_fieldnames(review_sample, REQUIRED_REVIEW_FIELDS + ("text",)),
    )
    write_csv(
        output_dir / "reviewer_decision_template.csv",
        review_template_rows(review_sample),
        list(REVIEWER_TEMPLATE_FIELDS),
    )

    return {
        "manifest": manifest,
        "sampling_report": sampling_report,
        "review_sample": review_sample,
        "selected_by_bucket": selected_by_bucket,
    }
