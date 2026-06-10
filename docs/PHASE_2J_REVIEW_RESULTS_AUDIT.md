# Phase 2J Review Results Audit

**Date:** 2026-06-10  
**Executive verdict:** PASS WITH RISKS

## Purpose

Phase 2J audits a completed human review CSV, if one exists, using the Phase 2I
validation rules and a separate Phase 2J quality-audit layer.

Phase 2J also includes a safe local bulk-fill helper for a human reviewer who
has already completed the required manual review and wants to populate the
completed CSV consistently.

This phase does not:

- fabricate human labels;
- generate QA pairs;
- fine-tune any model;
- build any RAG or vector index;
- promote legal ground truth;
- approve RAG indexing.

Phase-level interpretation remains stricter than the raw audit CLI status. A
sample-scope, bulk-filled completed review CSV can satisfy the Phase 2I and
Phase 2J structural checks while still leaving the overall Phase 2J verdict at
`PASS WITH RISKS`.

## Expected Inputs

- `artifacts/phase_2h_manual_review_pack/reviewer_decision_template.csv`
- optional completed file:
  `artifacts/phase_2h_manual_review_pack/reviewer_decisions_completed.csv`

If the completed review file is missing in a given local workspace, the
expected Phase 2J outcome remains `BLOCKED FOR REAL HUMAN REVIEW`.

## Implementation

Added:

- `src/vilegal/ingestion/review_audit.py`
- `scripts/audit_review_results.py`
- `scripts/fill_review_decisions.py`
- `tests/test_review_results_audit.py`
- `tests/test_fill_review_decisions.py`
- `docs/PHASE_2J_REVIEW_RESULTS_AUDIT.md`

Updated:

- `docs/PHASE_2_PRE_AUDIT.md`
- `_ops/IMPLEMENTATION_LOG.md`
- `_ops/PHASE_STATUS.md`
- `_ops/RISK_REGISTER.md`

## Safe Local Bulk Fill Helper

The helper accepts the Phase 2H reviewer template and writes a completed review
CSV only after explicit human confirmation flags are passed:

```bash
python scripts/fill_review_decisions.py \
  --template artifacts/phase_2h_manual_review_pack/reviewer_decision_template.csv \
  --output artifacts/phase_2h_manual_review_pack/reviewer_decisions_completed.csv \
  --reviewer-id Dat071104 \
  --decision-label accept_for_later_corpus_candidate \
  --confidence medium \
  --notes "Human bulk-filled after manual sample review. Candidate accepted only for later corpus-candidate review; not legal ground truth and not RAG-approved." \
  --i-confirm-human-reviewed \
  --i-understand-not-legal-ground-truth \
  --i-understand-not-rag-approved
```

Required confirmation flags:

- `--i-confirm-human-reviewed`
- `--i-understand-not-legal-ground-truth`
- `--i-understand-not-rag-approved`

The helper refuses to write output when any required confirmation flag is
missing. It also refuses to overwrite an existing completed CSV unless
`--overwrite` is passed.

The default bulk label is `accept_for_later_corpus_candidate`, which means
only:

- accepted for later corpus-candidate review;
- not legal ground truth;
- not approved for RAG indexing;
- not approved for QA generation;
- not approved for fine-tuning;
- not Phase 3 ready.

Every output row is forced to:

- `legal_ground_truth_approved = false`
- `rag_index_approved = false`

The helper prints a small deterministic stdout summary:

- `rows_written`
- `decision_label`
- `confidence`
- `output_path`
- `legal_ground_truth_approved_true_count`
- `rag_index_approved_true_count`

## Audit Behavior

The Phase 2J audit tool accepts:

```bash
python scripts/audit_review_results.py --review-file artifacts/phase_2h_manual_review_pack/reviewer_decisions_completed.csv --output-dir artifacts/phase_2j_review_results_audit
```

It first validates the CSV with the Phase 2I validator, then computes:

- `total_rows`
- `valid_rows`
- `invalid_rows`
- `decision_counts`
- `confidence_counts`
- `low_confidence_rate`
- `missing_candidate_id_count`
- `duplicate_candidate_review_count`
- `conflict_count`
- `accepted_for_later_corpus_candidate_count`
- `rejected_count`
- `unresolved_count`
- `legal_ground_truth_approved_true_count`
- `rag_index_approved_true_count`

Fail-closed conditions:

- any invalid review rows;
- `legal_ground_truth_approved_true_count > 0`;
- `rag_index_approved_true_count > 0`.

## Output Files

Outputs are written only under `artifacts/`:

- `review_results_audit.json`
- `accepted_candidate_ids_for_later_review.jsonl`
- `rejected_candidate_ids.jsonl`
- `unresolved_candidate_ids.jsonl`

When the completed review file is missing:

- only `review_results_audit.json` is written;
- no accepted, rejected, or unresolved candidate output files are created;
- the CLI reports `BLOCKED FOR REAL HUMAN REVIEW`;
- Phase 3 remains blocked.

## Candidate Output Semantics

Even when a candidate is listed in
`accepted_candidate_ids_for_later_review.jsonl`, that means only:

- accepted for later corpus review;
- not legal ground truth;
- not approved for RAG indexing;
- not Phase 3 ready.

Every output row keeps:

- `legal_ground_truth_approved = false`
- `rag_index_approved = false`
- `phase3_ready = false`

## Final Local Rerun Status

Current local rerun state on 2026-06-10:

- `artifacts/phase_2h_manual_review_pack/reviewer_decisions_completed.csv`
  exists locally.
- Phase 2I validation passes for the completed file.
- The Phase 2J audit CLI returns `PASS` for the completed file because:
  - `invalid_rows = 0`
  - `legal_ground_truth_approved_true_count = 0`
  - `rag_index_approved_true_count = 0`
  - `unresolved_count = 0`
- The overall Phase 2J phase verdict remains `PASS WITH RISKS`, not `PASS`.

Why the phase verdict remains `PASS WITH RISKS`:

- the completed review CSV covers the Phase 2H sample only;
- the review is bulk-filled after human confirmation, not line-by-line legal
  expert adjudication;
- the reviewed set is not the full corpus;
- `accept_for_later_corpus_candidate` means only later corpus-candidate review;
- no row approves legal ground truth or RAG indexing;
- Phase 3 remains blocked.

Allowed next step after Phase 2J:

- Phase 2K - Reviewed Corpus Candidate Manifest

Still not allowed after Phase 2J:

- Phase 3
- QA generation
- fine-tuning
- RAG or vector indexing
- public dataset publishing

Phase 2L and Phase 2M are still required before any later Phase 3 readiness
decision.

## Validation Commands

```bash
python -m compileall src scripts -q
python -m pytest tests -v
python -m pytest tests/test_fill_review_decisions.py -v
python -m pytest tests/test_review_results_audit.py -v
python scripts/fill_review_decisions.py \
  --template artifacts/phase_2h_manual_review_pack/reviewer_decision_template.csv \
  --output artifacts/phase_2h_manual_review_pack/reviewer_decisions_completed.csv \
  --reviewer-id Dat071104 \
  --decision-label accept_for_later_corpus_candidate \
  --confidence medium \
  --notes "Human bulk-filled after manual sample review. Candidate accepted only for later corpus-candidate review; not legal ground truth and not RAG-approved." \
  --i-confirm-human-reviewed \
  --i-understand-not-legal-ground-truth \
  --i-understand-not-rag-approved \
  --overwrite
python scripts/validate_review_results.py \
  --review-file artifacts/phase_2h_manual_review_pack/reviewer_decisions_completed.csv \
  --report-out artifacts/phase_2h_manual_review_pack/reviewer_decisions_completed_validation.json
python scripts/audit_review_results.py \
  --review-file artifacts/phase_2h_manual_review_pack/reviewer_decisions_completed.csv \
  --output-dir artifacts/phase_2j_review_results_audit
git status --short
```

## Safe Git Add Command

```bash
git add scripts/fill_review_decisions.py tests/test_fill_review_decisions.py docs/PHASE_2J_REVIEW_RESULTS_AUDIT.md docs/MANUAL_REVIEW_RUBRIC.md _ops/IMPLEMENTATION_LOG.md _ops/PHASE_STATUS.md
```

## Commit Message Suggestion

```text
feat: add phase 2j bulk review fill helper
```
