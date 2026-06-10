# Phase 2I Review Results Workflow

**Date:** 2026-06-10  
**Executive verdict:** PASS

## Purpose

Phase 2I defines the import schema, validation rules, and adjudication workflow
for human reviewer decisions collected from the Phase 2H
`reviewer_decision_template.csv`.

This phase is still review-only:

- no QA generation;
- no fine-tuning;
- no RAG or vector indexing;
- no legal ground-truth promotion;
- no automatic corpus approval.

## Input Contract

Expected input file:

- `artifacts/phase_2h_manual_review_pack/reviewer_decision_template.csv`

Required fields:

- `reviewer_id`
- `review_date`
- `candidate_id`
- `decision_label`
- `confidence`
- `notes`
- `legal_ground_truth_approved`
- `rag_index_approved`

Accepted `decision_label` values:

- `accept_for_later_corpus_candidate`
- `reject_not_article`
- `reject_duplicate`
- `reject_too_short`
- `reject_too_long`
- `reject_missing_metadata`
- `needs_legal_expert_review`
- `needs_parser_fix`
- `uncertain`

Accepted `confidence` values:

- `high`
- `medium`
- `low`

## Validation Rules

Implemented in `src/vilegal/ingestion/review_results.py` and exposed by
`scripts/validate_review_results.py`.

The validator:

1. rejects missing required fields;
2. rejects missing `candidate_id`;
3. rejects unknown `decision_label` values;
4. rejects unknown `confidence` values;
5. requires `review_date` in ISO `YYYY-MM-DD` format;
6. requires reviewer notes to be present;
7. forces `legal_ground_truth_approved=false` in this phase by rejecting any
   truthy value;
8. forces `rag_index_approved=false` in this phase by rejecting any truthy
   value;
9. reports decision counts, confidence counts, distinct reviewers, and invalid
   row details.

This is fail-closed. A structurally invalid row does not become a partial
approval.

## Adjudication Workflow

Phase 2I defines candidate-level adjudication states without promoting any
candidate downstream.

Per `candidate_id`, the workflow groups all valid reviewer rows and assigns one
status:

- `consensus`
  Used when all reviewers give the same non-escalation label.
- `parser_fix_required`
  Used when any reviewer flags `needs_parser_fix`, because tooling defects must
  be resolved before later corpus review.
- `legal_expert_review_required`
  Used when any reviewer flags `needs_legal_expert_review`.
- `uncertain_requires_adjudication`
  Used when reviewers remain uncertain and no higher-priority parser or legal
  escalation applies.
- `label_conflict_requires_adjudication`
  Used when reviewers disagree across ordinary accept or reject labels.

Priority order:

1. `needs_parser_fix`
2. `needs_legal_expert_review`
3. `uncertain`
4. ordinary label conflict
5. ordinary consensus

## CLI Usage

Validate a completed review CSV:

```bash
python scripts/validate_review_results.py --review-file artifacts/phase_2h_manual_review_pack/reviewer_decisions_completed.csv
```

Optional JSON report:

```bash
python scripts/validate_review_results.py --review-file artifacts/phase_2h_manual_review_pack/reviewer_decisions_completed.csv --report-out artifacts/phase_2i_review_results_report.json
```

The CLI exits non-zero when invalid rows are present.

## Safety Boundaries

- `legal_ground_truth_approved` must remain `false`.
- `rag_index_approved` must remain `false`.
- No candidate is promoted to legal ground truth automatically.
- No candidate is approved for RAG indexing automatically.
- Phase 3 remains blocked.

## Validation Commands

```bash
python -m compileall src scripts -q
python -m pytest tests -v
python -m pytest tests/test_review_results.py -v
git status --short
```

## Safe Git Add Command

```bash
git add src/vilegal/ingestion/review_results.py scripts/validate_review_results.py tests/test_review_results.py docs/PHASE_2I_REVIEW_RESULTS_WORKFLOW.md
git add docs/PHASE_2_PRE_AUDIT.md _ops/IMPLEMENTATION_LOG.md _ops/PHASE_STATUS.md _ops/RISK_REGISTER.md
```

## Commit Message Suggestion

```text
feat: add phase 2i review results validation workflow
```
