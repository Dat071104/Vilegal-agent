# Decisions

This document tracks major project decisions. Operational notes live in `_ops/DECISION_LOG.md`.

## D001 - Use gated phase execution

**Date:** 2026-06-09  
**Decision:** Keep the project on a gated workflow: plan, implement, test, self-audit, report, then prepare a commit suggestion.  
**Rationale:** This keeps legal-data handling reviewable and reduces the chance of silent scope drift.  
**Status:** ACTIVE

## D002 - Replace the unconditional Phase 1 source recommendation

**Date:** 2026-06-09  
**Decision:** Replace the prior "proceed to Phase 2 with UTS_VLC and duyet/vietnamese-legal-instruct" conclusion with a conditional source posture.

### Revised source posture

1. `undertheseanlp/UTS_VLC`
   `CONFIRMED`: current Hugging Face license field is `mit`.
   `CONFIRMED`: current dataset scope is Constitution, Codes, and Laws only.
   `NEEDS MANUAL REVIEW`: downstream provenance and relicensing basis.

2. `th1nhng0/vietnamese-legal-documents`
   `CONFIRMED`: current Hugging Face license field is `cc-by-4.0`.
   `CONFIRMED`: broader coverage includes decrees, circulars, decisions, and other normative acts.
   `NEEDS MANUAL REVIEW`: downstream provenance and relicensing basis.

3. `duyet/vietnamese-legal-instruct`
   `CONFIRMED`: current Hugging Face license field is `cc-by-4.0`.
   `CONFIRMED`: generated from `th1nhng0/vietnamese-legal-documents`.
   `CONFIRMED`: generated instruction data is not ground truth legal text.
   `NEEDS MANUAL REVIEW`: downstream provenance and relicensing basis.

4. `thangvip/vietnamese-legal-qa`
   `CONFIRMED`: the dataset card does not provide a clean SPDX-style license field.
   `CONFIRMED`: generated QA data is not ground truth legal text.
   `NEEDS MANUAL REVIEW`: downstream license scope.

**Rationale:** The prior Phase 1 report contained stale license claims. The corrected posture is safer and matches the current dataset cards.

**Status:** ACTIVE

## D003 - Do not start Phase 2 implementation yet

**Date:** 2026-06-09  
**Decision:** Keep Phase 2 in pre-audit only. No ingestion pipeline, no scraping, no bulk download, and no external API calls are approved in this repo state.

### Allowed work

- Local schema hardening.
- Synthetic/example sample validation.
- Manual source and license review.
- A capped future sample-only ingestion plan with `--max-records 100`.

### Blocked work

- Bulk download from any dataset source.
- Any claim that VBPL API registration or restricted access is settled without repo-local official documentation.
- Treating generated instruction or QA datasets as authoritative legal truth.

**Rationale:** Provenance and licensing are not fully resolved for non-synthetic sources.

**Status:** ACTIVE - Phase 2 bulk download blocked, sample-only ingestion may be planned but not implemented.
