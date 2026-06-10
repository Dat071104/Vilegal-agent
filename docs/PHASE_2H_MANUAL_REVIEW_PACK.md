# Phase 2H Manual Review Pack

**Date:** 2026-06-10  
**Executive verdict:** PASS WITH RISKS

## Why Phase 2H Exists

Phase 2H creates a deterministic manual-review sampling pack from the existing
Phase 2G UTS filtering outputs. The goal is to help a human reviewer inspect
clean-ish candidates, review-only candidates, rejected candidates,
duplicate-related examples, suspicious-length examples, and provenance
completeness before any future corpus gate is discussed.

This phase is review-only:

- not Phase 3;
- not QA generation;
- not fine-tuning;
- not RAG or vector indexing;
- not legal-ground-truth approval.

## Input Artifacts

- `artifacts/phase_2g_uts_filtering/filtered_candidates.jsonl`
- `artifacts/phase_2g_uts_filtering/rejected_candidates.jsonl`
- `artifacts/phase_2g_uts_filtering/needs_review_candidates.jsonl`
- `artifacts/phase_2g_uts_filtering/filter_report.json`

No new ingestion is required for this phase.

## Output Artifacts

Generated only under ignored `artifacts/phase_2h_manual_review_pack/`:

- `review_sample.jsonl`
- `review_sample.csv`
- `review_manifest.json`
- `sampling_report.json`
- `duplicate_group_sample.jsonl`
- `suspicious_length_sample.jsonl`
- `reviewer_decision_template.csv`
- `keep_sample.jsonl`
- `needs_review_sample.jsonl`
- `rejected_sample.jsonl`

## Sampling Strategy

The sampler is deterministic.

- default `sample_size = 150`
- default `seed = 42`
- output path must stay under `artifacts/`
- existing Phase 2G artifacts are read-only

Target bucket mix:

- `keep_candidate_for_human_review`
- `needs_review`
- `rejected`
- `duplicate_related`
- `suspicious_length`

The implementation samples buckets disjointly, reports shortfalls explicitly,
and uses round-robin selection by `parent_record_id` where possible so the
review pack covers multiple parent documents instead of clustering on one
source document.

Parent-document warnings are preserved as metadata and intentionally
represented in the sample when available, but they do not auto-promote a
record into a separate approval state.

## Review Rubric

Reviewer instructions are defined in `docs/MANUAL_REVIEW_RUBRIC.md`.

## Metrics Summary From Measured Run

Measured from:

- `artifacts/phase_2h_manual_review_pack/sampling_report.json`
- `artifacts/phase_2h_manual_review_pack/review_manifest.json`

| Metric | Value |
|---|---|
| total_available_candidates | `20,393` |
| total_sampled | `150` |
| sampled_by_bucket | `duplicate_related=10`, `suspicious_length=10`, `keep_candidate_for_human_review=60`, `needs_review=50`, `rejected=20` |
| sampled_by_filter_decision | `keep=60`, `needs_review_marker_uncertainty=47`, `needs_review_suspicious_length=10`, `reject_duplicate_hash=20`, `reject_near_empty=13` |
| sampled_duplicate_examples | `10` |
| sampled_suspicious_length_examples | `10` |
| sampled_parent_warning_examples | `150` |
| source_datasets_covered | `undertheseanlp/UTS_VLC` |
| source_id_count | `128` |
| parent_documents_covered | `128` |
| sampling_seed | `42` |
| sample_size_requested | `150` |
| sample_size_actual | `150` |
| approved_for_rag_index_true_count | `0` |
| is_legal_ground_truth_true_count | `0` |
| safety_verdict | `PASS WITH RISKS` |

Interpretation:

- The sampler met the full requested `150` rows with no bucket shortfall.
- The sample covers `128` distinct parent documents.
- `sampled_parent_warning_examples = 150` reflects the current UTS parser state:
  most Phase 2F/2G parent documents carry a preserved preamble warning, so the
  review pack should treat that warning as metadata, not as legal invalidation.

## Known Risks

- Phase 2G already leaves many candidates in review-only state, so this pack
  is an inspection aid, not a clean corpus.
- Duplicate-related examples still exist and require human judgment.
- Suspicious-length examples still require human judgment.
- Parent-document warnings remain metadata carried from parser outputs and
  cannot be treated as legal defects by themselves.
- Candidate text must not be treated as legally authoritative.
- Human review quality can vary across reviewers.

## Why Phase 3 Remains Blocked

The review pack does not approve any candidate for:

- legal ground truth;
- QA generation;
- fine-tuning;
- RAG or vector indexing;
- public dataset publication.

Phase 3 remains blocked until a later human gate explicitly approves a
narrower downstream use case.

## Validation Commands

```bash
python -m compileall src scripts -q
python -m pytest tests -v
python -m pytest tests/test_review_sampler.py -v
python scripts/build_phase2h_review_pack.py --input-dir artifacts/phase_2g_uts_filtering --output-dir artifacts/phase_2h_manual_review_pack --sample-size 150 --seed 42
git status --short
```

## Safe Git Add Command

```bash
git add docs/PHASE_2H_MANUAL_REVIEW_PACK.md docs/MANUAL_REVIEW_RUBRIC.md scripts/build_phase2h_review_pack.py src/vilegal/ingestion/review_sampler.py tests/test_review_sampler.py
git add docs/PHASE_2_PRE_AUDIT.md _ops/IMPLEMENTATION_LOG.md _ops/PHASE_STATUS.md _ops/RISK_REGISTER.md
```

## Commit Message Suggestion

```text
feat: add phase 2h manual review sampling pack
```
