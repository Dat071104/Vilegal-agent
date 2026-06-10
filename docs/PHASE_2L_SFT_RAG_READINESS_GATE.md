# Phase 2L SFT/RAG Readiness Gate

**Date:** 2026-06-10  
**Executive verdict:** PASS WITH RISKS

## Purpose

Phase 2L evaluates whether the current reviewed sample subset is ready for:

- continued corpus review planning;
- QA or SFT preparation;
- RAG indexing;
- Phase 3 scaffold planning only.

This phase does not:

- generate QA pairs;
- fine-tune any model;
- build a RAG or vector index;
- publish datasets;
- start Phase 3 execution.

## Inputs

- `artifacts/phase_2k_corpus_candidate_manifest/manifest_report.json`
- `artifacts/phase_2k_corpus_candidate_manifest/corpus_candidate_manifest.jsonl`
- `docs/ATTRIBUTION.md`
- `docs/DATA_USE_POLICY.md`
- `docs/PHASE_2J_REVIEW_RESULTS_AUDIT.md`
- `docs/PHASE_2K_CORPUS_CANDIDATE_MANIFEST.md`

## Implementation

Added:

- `src/vilegal/ingestion/readiness_gate.py`
- `scripts/check_phase3_readiness.py`
- `tests/test_phase3_readiness.py`
- `docs/PHASE_2L_SFT_RAG_READINESS_GATE.md`

Updated:

- `docs/PHASE_2_PRE_AUDIT.md`
- `_ops/IMPLEMENTATION_LOG.md`
- `_ops/PHASE_STATUS.md`
- `_ops/RISK_REGISTER.md`

## Checks

The readiness gate checks:

- manifest exists;
- manifest rows remain sample-scope only;
- accepted candidate count is non-zero;
- unique parent-document coverage is non-zero;
- provenance coverage is complete;
- attribution docs are present;
- data-use policy doc is present;
- license fields are present;
- `legal_ground_truth_true_count == 0`;
- `rag_index_approved_true_count == 0`;
- `qa_generation_approved_true_count == 0`;
- `fine_tuning_approved_true_count == 0`;
- `phase3_ready_true_count == 0`;
- review coverage limits are documented;
- bulk-review limits are documented.

## Outputs

The readiness report writes:

- `corpus_candidate_manifest_ready`
- `qa_generation_ready`
- `fine_tuning_ready`
- `rag_indexing_ready`
- `phase3_scaffold_ready`
- `required_before_training`
- `required_before_rag`
- `readiness_verdict`

## Current Local Run

Current local run on 2026-06-10:

- `corpus_candidate_manifest_ready = true`
- `qa_generation_ready = false`
- `fine_tuning_ready = false`
- `rag_indexing_ready = false`
- `phase3_scaffold_ready = true`
- `readiness_verdict = PASS WITH RISKS`

Detailed checks:

- `manifest_exists = true`
- `manifest_sample_scope_only = true`
- `accepted_candidate_count = 150`
- `unique_parent_documents = 128`
- `provenance_coverage = 1.0`
- `attribution_docs_present = true`
- `data_use_policy_present = true`
- `license_fields_present = true`
- `legal_ground_truth_true_count = 0`
- `rag_index_approved_true_count = 0`
- `qa_generation_approved_true_count = 0`
- `fine_tuning_approved_true_count = 0`
- `phase3_ready_true_count = 0`
- `review_coverage_limitation_documented = true`
- `bulk_review_limitation_documented = true`

## Interpretation

What Phase 2L allows:

- continued corpus-review planning;
- Phase 3 scaffold planning only.

What Phase 2L still blocks:

- QA generation;
- SFT or fine-tuning;
- RAG indexing;
- any claim that the reviewed sample is a full approved corpus.

Why the verdict remains `PASS WITH RISKS`:

- the manifest is valid, but it still covers the Phase 2H sample only;
- no downstream approval exists for QA, training, or RAG;
- Phase 3 may be planned only as scaffold work, not executed as training or indexing.

## Required Before Training

- Expand beyond the Phase 2H sample to a broader reviewed corpus.
- Complete a later training-data gate with explicit QA/SFT approval.
- Keep legal-ground-truth and provenance decisions explicitly reviewed by humans.
- Approve downstream use separately from sample-scope corpus candidacy.

## Required Before RAG

- Expand beyond the Phase 2H sample to a broader reviewed corpus.
- Approve RAG indexing explicitly after a later corpus-review gate.
- Validate citation and provenance behavior on the selected corpus subset.
- Keep attribution and license obligations attached to downstream artifacts.

## Validation Commands

```bash
python -m compileall src scripts -q
python -m pytest tests -v
python -m pytest tests/test_phase3_readiness.py -v
python scripts/check_phase3_readiness.py --manifest-dir artifacts/phase_2k_corpus_candidate_manifest --report-out artifacts/phase_2l_phase3_readiness_report.json
git status --short
```

## Safe Git Add Command

```bash
git add src/vilegal/ingestion/readiness_gate.py scripts/check_phase3_readiness.py tests/test_phase3_readiness.py docs/PHASE_2L_SFT_RAG_READINESS_GATE.md docs/PHASE_2_PRE_AUDIT.md _ops/IMPLEMENTATION_LOG.md _ops/PHASE_STATUS.md _ops/RISK_REGISTER.md
```

## Commit Message Suggestion

```text
feat: add phase 2l sft rag readiness gate
```
