# Manual Review Rubric

**Phase:** Phase 2H - Manual Review Pack / Sampling Audit  
**Status:** REVIEW-ONLY

## Reviewer Purpose

This rubric guides human review of Phase 2G UTS article candidates that were sampled into the Phase 2H manual-review pack.

Reviewers are inspecting parser and filter outputs only. They are not giving legal advice, legal interpretation, or legal certification.

## What Reviewers May Decide

Reviewers may label whether a sampled candidate appears structurally usable for a later corpus-candidate review queue.

Allowed labels:

- `accept_for_later_corpus_candidate`
- `reject_not_article`
- `reject_duplicate`
- `reject_too_short`
- `reject_too_long`
- `reject_missing_metadata`
- `needs_legal_expert_review`
- `needs_parser_fix`
- `uncertain`

## What Reviewers May Not Decide

Reviewers may not:

- declare the text legally authoritative;
- approve any record for RAG indexing;
- approve any record for fine-tuning;
- infer legal correctness from formatting alone;
- start Phase 3 work from this pack.

Accepting a candidate for later corpus review does not approve it for RAG, QA generation, training, or publication.

## Label Definitions

- `accept_for_later_corpus_candidate`: candidate appears article-like, provenance is present, and no obvious parser/filter defect blocks later corpus review.
- `reject_not_article`: candidate does not appear to be a real article or usable article chunk.
- `reject_duplicate`: candidate is a repeated segment that should not proceed as an independent corpus candidate.
- `reject_too_short`: candidate is too short to support reliable later review.
- `reject_too_long`: candidate is too long or likely spans multiple structural units.
- `reject_missing_metadata`: required provenance or review metadata is incomplete.
- `needs_legal_expert_review`: structure looks plausible, but legal interpretation or legal status cannot be resolved in this phase.
- `needs_parser_fix`: candidate appears harmed by parser or filter behavior and should be re-checked at the tooling level.
- `uncertain`: reviewer cannot confidently classify the candidate.

## Required Review Fields

Every reviewer row must include:

- `reviewer_id`
- `review_date`
- `candidate_id`
- `decision_label`
- `confidence`
- `notes`
- `legal_ground_truth_approved`
- `rag_index_approved`

Allowed confidence values:

- `high`
- `medium`
- `low`

Recommended default for safe bulk fill:

- `medium`

Use `medium` for bulk-filled rows unless the reviewer is intentionally making a
different confidence call. Bulk fill is an operational convenience only; it is
not line-by-line legal expert adjudication.

## Safe Bulk Fill Helper

If the reviewer has already completed the required manual sample review and
wants to populate the completed CSV locally, use:

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

This helper is safe only because it requires explicit human confirmation flags
before writing any output.

The helper does not:

- approve legal ground truth;
- approve RAG indexing;
- approve QA generation;
- approve fine-tuning;
- unblock Phase 3.

The default bulk label `accept_for_later_corpus_candidate` means only:

- accepted for later corpus-candidate review;
- not legally authoritative;
- not approved for RAG;
- not approved for QA or fine-tuning.

## Safety Boundaries

- `legal_ground_truth_approved` must remain `false`.
- `rag_index_approved` must remain `false`.
- Candidates remain parser/filter outputs only.
- Phase 3 remains blocked.
- Phase 2K is not started by this helper.
- No QA generation is allowed from this review pack.
- No fine-tuning is allowed from this review pack.
- No RAG or vector indexing is allowed from this review pack.

## Reviewer Reminder

This phase only prepares evidence for later human gates. It does not create a legal corpus, does not create legal ground truth, and does not authorize any downstream deployment use.
