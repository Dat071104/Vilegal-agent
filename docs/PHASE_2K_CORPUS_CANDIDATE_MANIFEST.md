# Phase 2K Corpus Candidate Manifest

**Date:** 2026-06-10  
**Executive verdict:** PASS WITH RISKS

## Purpose

Phase 2K builds a deterministic manifest for reviewed, sample-scope corpus
candidate records only.

This phase does not:

- approve the full corpus;
- promote legal ground truth;
- approve QA generation;
- approve fine-tuning;
- approve RAG indexing;
- start Phase 3.

Every manifest row remains sample-scope only and keeps downstream approval
flags forced to `false`.

## Inputs

- `artifacts/phase_2h_manual_review_pack/reviewer_decisions_completed.csv`
- `artifacts/phase_2j_review_results_audit/accepted_candidate_ids_for_later_review.jsonl`
- `artifacts/phase_2h_manual_review_pack/review_sample.jsonl`
- `artifacts/phase_2g_uts_filtering/filtered_candidates.jsonl`
- `artifacts/phase_2g_uts_filtering/needs_review_candidates.jsonl`
- `artifacts/phase_2g_uts_filtering/rejected_candidates.jsonl`

## Implementation

Added:

- `src/vilegal/ingestion/corpus_manifest.py`
- `scripts/build_corpus_candidate_manifest.py`
- `tests/test_corpus_manifest.py`
- `docs/PHASE_2K_CORPUS_CANDIDATE_MANIFEST.md`

Updated:

- `docs/PHASE_2_PRE_AUDIT.md`
- `_ops/IMPLEMENTATION_LOG.md`
- `_ops/PHASE_STATUS.md`
- `_ops/RISK_REGISTER.md`

## Manifest Semantics

Each manifest record preserves:

- `candidate_id`
- `parent_record_id`
- `source_dataset`
- `source_id`
- `source_url`
- `license`
- `title`
- `article_number`
- `article_title`
- `text_hash`
- `parser_version`
- `filter_version`
- `reviewer_id`
- `review_date`
- `decision_label`
- `confidence`

Each manifest record also sets:

- `review_scope = "phase_2h_sample_only"`
- `approval_scope = "later_corpus_candidate_review_only"`
- `is_legal_ground_truth = false`
- `approved_for_rag_index = false`
- `approved_for_qa_generation = false`
- `approved_for_fine_tuning = false`
- `phase3_ready = false`

The accepted Phase 2J decision means only:

- accepted for later corpus-candidate review;
- not legal ground truth;
- not QA approved;
- not fine-tuning approved;
- not RAG approved;
- not Phase 3 ready.

## Output Files

Outputs are written only under `artifacts/phase_2k_corpus_candidate_manifest/`:

- `corpus_candidate_manifest.json`
- `corpus_candidate_manifest.jsonl`
- `manifest_report.json`
- optional `rejected_from_manifest.jsonl`
- optional `unresolved_from_manifest.jsonl`

## Fail-Closed and Reporting Rules

Fail-closed conditions:

- missing accepted-ID input file;
- missing completed review CSV;
- missing review sample input file;
- missing required Phase 2G filter files;
- missing review metadata for an accepted candidate;
- review metadata that contradicts the accepted Phase 2J decision;
- any downstream approval flag or legal-ground-truth flag becoming `true`;
- count reconciliation failure.

Reported, but not automatically fail-closed:

- missing filter metadata for an accepted candidate.

When filter metadata is missing, the candidate is written to
`unresolved_from_manifest.jsonl` instead of being dropped silently.

## Current Local Run Metrics

Current local run on 2026-06-10:

- `accepted_candidate_ids_input_count = 150`
- `manifest_records_written = 150`
- `missing_review_metadata_count = 0`
- `missing_filter_metadata_count = 0`
- `rejected_from_manifest_count = 0`
- `unresolved_from_manifest_count = 0`
- `unique_parent_documents = 128`
- `unique_source_ids = 128`
- `decision_counts = {"accept_for_later_corpus_candidate": 150}`
- `confidence_counts = {"medium": 150}`
- `legal_ground_truth_true_count = 0`
- `rag_index_approved_true_count = 0`
- `qa_generation_approved_true_count = 0`
- `fine_tuning_approved_true_count = 0`
- `phase3_ready_true_count = 0`
- `manifest_verdict = PASS WITH RISKS`

Why the verdict remains `PASS WITH RISKS`:

- the reviewed set is the Phase 2H sample only;
- all accepted rows still mean later corpus-candidate review only;
- no legal-ground-truth approval exists;
- no QA, fine-tuning, or RAG approval exists;
- Phase 3 remains blocked pending Phase 2L and Phase 2M.

## Validation Commands

```bash
python -m compileall src scripts -q
python -m pytest tests -v
python -m pytest tests/test_corpus_manifest.py -v
python scripts/build_corpus_candidate_manifest.py --review-audit-dir artifacts/phase_2j_review_results_audit --review-pack-dir artifacts/phase_2h_manual_review_pack --filter-dir artifacts/phase_2g_uts_filtering --output-dir artifacts/phase_2k_corpus_candidate_manifest
git status --short
```

## Safe Git Add Command

```bash
git add src/vilegal/ingestion/corpus_manifest.py scripts/build_corpus_candidate_manifest.py tests/test_corpus_manifest.py docs/PHASE_2K_CORPUS_CANDIDATE_MANIFEST.md docs/PHASE_2_PRE_AUDIT.md _ops/IMPLEMENTATION_LOG.md _ops/PHASE_STATUS.md _ops/RISK_REGISTER.md
```

## Commit Message Suggestion

```text
feat: add phase 2k reviewed corpus candidate manifest
```
