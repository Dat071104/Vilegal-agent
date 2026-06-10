"""
readiness_gate.py - Phase 2L readiness gate for later Phase 3 decisions.

Evaluates whether the reviewed sample-scope manifest is structurally ready for
continued corpus review and Phase 3 scaffold planning. This module never
approves QA generation, fine-tuning, or RAG indexing.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

PHASE_NAME = "Phase 2L - SFT/RAG Readiness Gate"
READINESS_VERSION = "phase_2l_v1"
BLOCKED_STATUS = "BLOCKED FOR FULL CORPUS REVIEW"


@dataclass
class ReadinessChecks:
    manifest_exists: bool
    manifest_sample_scope_only: bool
    accepted_candidate_count: int
    unique_parent_documents: int
    provenance_coverage: float
    attribution_docs_present: bool
    data_use_policy_present: bool
    license_fields_present: bool
    legal_ground_truth_true_count: int
    rag_index_approved_true_count: int
    qa_generation_approved_true_count: int
    fine_tuning_approved_true_count: int
    phase3_ready_true_count: int
    review_coverage_limitation_documented: bool
    bulk_review_limitation_documented: bool


@dataclass
class ReadinessReport:
    phase: str
    readiness_version: str
    manifest_dir: str
    manifest_report_path: str
    manifest_jsonl_path: str
    corpus_candidate_manifest_ready: bool
    qa_generation_ready: bool
    fine_tuning_ready: bool
    rag_indexing_ready: bool
    phase3_scaffold_ready: bool
    required_before_training: list[str] = field(default_factory=list)
    required_before_rag: list[str] = field(default_factory=list)
    readiness_verdict: str = "FAIL"
    reason: str = ""
    checks: ReadinessChecks | None = None


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


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def provenance_coverage(records: list[dict[str, Any]]) -> float:
    if not records:
        return 0.0
    covered = 0
    for record in records:
        has_source_ref = bool(
            normalize_text(record.get("source_id")) or normalize_text(record.get("source_url"))
        )
        if all(
            [
                normalize_text(record.get("candidate_id")),
                normalize_text(record.get("parent_record_id")),
                normalize_text(record.get("source_dataset")),
                normalize_text(record.get("license")),
                normalize_text(record.get("text_hash")),
                normalize_text(record.get("parser_version")),
                normalize_text(record.get("filter_version")),
                has_source_ref,
            ]
        ):
            covered += 1
    return round(covered / len(records), 6)


def report_to_dict(report: ReadinessReport) -> dict[str, Any]:
    return {
        "phase": report.phase,
        "readiness_version": report.readiness_version,
        "manifest_dir": report.manifest_dir,
        "manifest_report_path": report.manifest_report_path,
        "manifest_jsonl_path": report.manifest_jsonl_path,
        "corpus_candidate_manifest_ready": report.corpus_candidate_manifest_ready,
        "qa_generation_ready": report.qa_generation_ready,
        "fine_tuning_ready": report.fine_tuning_ready,
        "rag_indexing_ready": report.rag_indexing_ready,
        "phase3_scaffold_ready": report.phase3_scaffold_ready,
        "required_before_training": report.required_before_training,
        "required_before_rag": report.required_before_rag,
        "readiness_verdict": report.readiness_verdict,
        "reason": report.reason,
        "checks": asdict(report.checks) if report.checks is not None else None,
    }


def check_phase3_readiness(
    *,
    manifest_dir: Path,
    attribution_path: Path,
    data_use_policy_path: Path,
    phase2j_doc_path: Path,
    phase2k_doc_path: Path,
) -> ReadinessReport:
    manifest_report_path = manifest_dir / "manifest_report.json"
    manifest_jsonl_path = manifest_dir / "corpus_candidate_manifest.jsonl"
    manifest_exists = manifest_report_path.exists() and manifest_jsonl_path.exists()

    manifest_rows: list[dict[str, Any]] = []
    manifest_report: dict[str, Any] = {}
    if manifest_exists:
        manifest_rows = load_jsonl(manifest_jsonl_path)
        manifest_report = load_json(manifest_report_path)

    phase2j_text = phase2j_doc_path.read_text(encoding="utf-8") if phase2j_doc_path.exists() else ""
    phase2k_text = phase2k_doc_path.read_text(encoding="utf-8") if phase2k_doc_path.exists() else ""
    combined_text = f"{phase2j_text}\n{phase2k_text}"

    sample_scope_only = bool(manifest_rows) and all(
        normalize_text(row.get("review_scope")) == "phase_2h_sample_only"
        and normalize_text(row.get("approval_scope")) == "later_corpus_candidate_review_only"
        for row in manifest_rows
    )
    accepted_candidate_count = int(
        (manifest_report.get("metrics") or {}).get("manifest_records_written") or len(manifest_rows)
    )
    unique_parent_documents = int(
        (manifest_report.get("metrics") or {}).get("unique_parent_documents") or len(
            {
                normalize_text(row.get("parent_record_id"))
                for row in manifest_rows
                if normalize_text(row.get("parent_record_id"))
            }
        )
    )
    coverage = provenance_coverage(manifest_rows)
    license_fields_present = bool(manifest_rows) and all(
        normalize_text(row.get("license")) for row in manifest_rows
    )
    legal_ground_truth_true_count = sum(
        1 for row in manifest_rows if bool(row.get("is_legal_ground_truth")) is True
    )
    rag_true_count = sum(1 for row in manifest_rows if bool(row.get("approved_for_rag_index")) is True)
    qa_true_count = sum(
        1 for row in manifest_rows if bool(row.get("approved_for_qa_generation")) is True
    )
    fine_tuning_true_count = sum(
        1 for row in manifest_rows if bool(row.get("approved_for_fine_tuning")) is True
    )
    phase3_ready_true_count = sum(1 for row in manifest_rows if bool(row.get("phase3_ready")) is True)
    review_coverage_limitation_documented = (
        contains_any(combined_text, ("sample-scope", "sample scope", "phase 2h sample", "sample only"))
        and contains_any(combined_text, ("full corpus", "not the full corpus", "not full-corpus", "not full corpus"))
    )
    bulk_review_limitation_documented = contains_any(
        phase2j_text,
        ("bulk-filled", "bulk fill", "bulk-filled after human confirmation"),
    )

    checks = ReadinessChecks(
        manifest_exists=manifest_exists,
        manifest_sample_scope_only=sample_scope_only,
        accepted_candidate_count=accepted_candidate_count,
        unique_parent_documents=unique_parent_documents,
        provenance_coverage=coverage,
        attribution_docs_present=attribution_path.exists(),
        data_use_policy_present=data_use_policy_path.exists(),
        license_fields_present=license_fields_present,
        legal_ground_truth_true_count=legal_ground_truth_true_count,
        rag_index_approved_true_count=rag_true_count,
        qa_generation_approved_true_count=qa_true_count,
        fine_tuning_approved_true_count=fine_tuning_true_count,
        phase3_ready_true_count=phase3_ready_true_count,
        review_coverage_limitation_documented=review_coverage_limitation_documented,
        bulk_review_limitation_documented=bulk_review_limitation_documented,
    )

    required_before_training = [
        "Expand beyond the Phase 2H sample to a broader reviewed corpus.",
        "Complete a later training-data gate with explicit QA/SFT approval.",
        "Keep legal-ground-truth and provenance decisions explicitly reviewed by humans.",
        "Approve downstream use separately from sample-scope corpus candidacy.",
    ]
    required_before_rag = [
        "Expand beyond the Phase 2H sample to a broader reviewed corpus.",
        "Approve RAG indexing explicitly after a later corpus-review gate.",
        "Validate citation and provenance behavior on the selected corpus subset.",
        "Keep attribution and license obligations attached to downstream artifacts.",
    ]

    hard_fail = (
        not manifest_exists
        or legal_ground_truth_true_count > 0
        or rag_true_count > 0
        or qa_true_count > 0
        or fine_tuning_true_count > 0
        or phase3_ready_true_count > 0
    )
    corpus_manifest_ready = (
        manifest_exists
        and sample_scope_only
        and accepted_candidate_count > 0
        and unique_parent_documents > 0
        and coverage == 1.0
        and attribution_path.exists()
        and data_use_policy_path.exists()
        and license_fields_present
        and legal_ground_truth_true_count == 0
        and rag_true_count == 0
        and qa_true_count == 0
        and fine_tuning_true_count == 0
        and phase3_ready_true_count == 0
    )
    phase3_scaffold_ready = (
        corpus_manifest_ready
        and review_coverage_limitation_documented
        and bulk_review_limitation_documented
    )

    if hard_fail:
        verdict = "FAIL"
        reason = "Readiness gate failed because the manifest is missing or forbidden downstream approval flags were detected."
    elif not phase3_scaffold_ready:
        verdict = BLOCKED_STATUS
        reason = "Sample-scope review limits or documentation gaps prevent even scaffold-only Phase 3 planning."
    else:
        verdict = "PASS WITH RISKS"
        reason = "Manifest tooling is valid for scaffold planning only, but QA, fine-tuning, and RAG indexing remain blocked."

    return ReadinessReport(
        phase=PHASE_NAME,
        readiness_version=READINESS_VERSION,
        manifest_dir=str(manifest_dir.resolve()),
        manifest_report_path=str(manifest_report_path.resolve()),
        manifest_jsonl_path=str(manifest_jsonl_path.resolve()),
        corpus_candidate_manifest_ready=corpus_manifest_ready,
        qa_generation_ready=False,
        fine_tuning_ready=False,
        rag_indexing_ready=False,
        phase3_scaffold_ready=phase3_scaffold_ready,
        required_before_training=required_before_training,
        required_before_rag=required_before_rag,
        readiness_verdict=verdict,
        reason=reason,
        checks=checks,
    )
