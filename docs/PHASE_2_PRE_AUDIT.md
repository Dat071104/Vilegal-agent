# Phase 2 Pre-Audit

**Date:** 2026-06-09
**Status:** HISTORICAL PRE-AUDIT
**Implementation status:** Superseded by Phases 2A through 2G. Sample-only ingestion scaffold, parser candidates, and filtering rules are now implemented. Offline fixture dry-run: PASS.

## Objective

Define the exact gates that must pass before any Phase 2 ingestion work is implemented.

## In scope for a future Phase 2 start

1. Sample-only ingestion from already identified sources.
2. Record-level provenance capture in the local schema.
3. Quality instrumentation for parsing and metadata completeness.
4. A safety default of `--max-records 100`.
5. Attribution handling for any CC-BY-4.0 source used in samples.

## Out of scope

1. Bulk dataset download.
2. VBPL scraping or API integration.
3. Model training or fine-tuning.
4. Vector indexing or retrieval implementation.
5. Any production or legal conclusion about upstream relicensing rights.

## Source posture for Phase 2 planning

- `undertheseanlp/UTS_VLC`
  `CONFIRMED`: cleanest limited corpus candidate.
  `CONFIRMED`: Constitution, Codes, and Laws only.
  `NEEDS MANUAL REVIEW`: provenance and relicensing basis.

- `th1nhng0/vietnamese-legal-documents`
  `CONFIRMED`: broad coverage of laws and sub-law instruments.
  `CONFIRMED`: current Hugging Face card lists `cc-by-4.0`.
  `NEEDS MANUAL REVIEW`: provenance and relicensing basis.

- `duyet/vietnamese-legal-instruct`
  `CONFIRMED`: generated instruction dataset.
  `CONFIRMED`: current Hugging Face card lists `cc-by-4.0`.
  `NEEDS MANUAL REVIEW`: provenance and relicensing basis.

- `thangvip/vietnamese-legal-qa`
  `CONFIRMED`: generated QA dataset.
  `NEEDS MANUAL REVIEW`: exact downstream license scope.

## Go or no-go gates before any bulk download

All gates below must pass before bulk download is allowed:

1. License capture gate
   Every candidate dataset must have its current license field recorded with a retrieval date.

2. Attribution gate
   Every CC-BY-4.0 candidate must have a written attribution template stored in the repo docs.

3. Provenance gate
   Human review must sign off on the upstream source chain and downstream relicensing risk for each non-synthetic dataset.

4. Coverage gate
   The project must document which document types each source does and does not cover.

5. Schema gate
   Every ingested record must carry source dataset, source id or source URL, license, retrieved-at timestamp, effective status, document type, document number, article number when applicable, and text.

6. Dry-run gate
   A future sample-only dry run must use `--max-records 100` or less and stay within the quality thresholds below.

7. Storage gate
   Raw datasets, processed bulk outputs, model files, cache folders, and tokens must remain excluded from git.

## Quality metrics for a future sample-only dry run

These metrics must be measured before any bulk ingestion is approved:

| Metric | Definition | Target |
|---|---|---|
| Parse success rate | Share of records that validate against the chosen schema | `>= 99%` |
| Empty text rate | Share of records with blank or whitespace-only text after normalization | `<= 0.5%` |
| Duplicate rate | Share of duplicate records by source id plus article number plus text hash | `<= 2%` |
| Missing metadata rate | Share of records missing required provenance or document metadata fields | `<= 1%` |
| License or provenance coverage | Share of records inheriting a reviewed source dataset, license label, and retrieval timestamp | `100%` |
| Malformed article or clause rate | Share of records with invalid article numbering, invalid clause numbering, or broken nesting | `<= 1%` |

## Default safety controls for any future implementation

1. Keep the default limit at `--max-records 100`.
2. Require an explicit override to exceed the default.
3. Write sample outputs only to ignored paths.
4. Log the source dataset, license, and retrieval date for every run.
5. Fail closed when license or provenance fields are missing.

## Recommendation

- Phase 2A sample-only scaffold: **COMPLETE — PASS**
- Phase 2B online smoke test: **COMPLETE — PASS WITH DISCOVERIES**
  - UTS_VLC: 10/10 normalized, quality gate PASS. Uses year-based splits (e.g. `2026`), not `train`.
  - duyet/vietnamese-legal-instruct: 10/10 normalized after conversations-format normalizer fix. CC-BY-4.0 attribution confirmed and preserved.
  - th1nhng0/vietnamese-legal-documents: DEFERRED (not required to attempt; resources saved).
- Phase 2C human gate pack: **COMPLETE — PASS**
  - Documents created: `ATTRIBUTION.md`, `DATA_USE_POLICY.md`, `BULK_INGESTION_GATE.md`.
- Phase 2 bulk download: **NO-GO** (unchanged)
- Phase 2D implementation: **COMPLETE — PASS WITH RISKS**. Controlled pilot successfully pulled `uts_vlc` and `duyet_legal_instruct` up to 1000 records. `th1nhng0_legal_documents` deferred due to HF dataset config issues. No generated data tracked.
- Phase 2E implementation: **COMPLETE - PASS WITH RISKS**
  - `UTS_VLC`: content is viable as a document-level legal corpus candidate only. Current normalized output does not preserve article-level metadata.
  - `duyet_legal_instruct`: normalized `text` correctly remains the user query; assistant answers remain in `raw_metadata` only. This source is still generated supervision, not legal ground truth.
  - Downstream readiness:
    - RAG corpus readiness: `PASS WITH RISKS` for `UTS_VLC` only
    - SFT dataset readiness: `BLOCKED`
    - Evaluation dataset readiness: `BLOCKED`
    - Public release readiness: `BLOCKED`
  - Phase 3: **DO NOT START**.
- Phase 2F implementation: **COMPLETE - PASS WITH RISKS**
  - Secondary parser created for existing document-level `UTS_VLC` outputs only.
  - Derived article/chunk records are parser candidates only, not legal ground truth.
  - All derived candidates are marked `approved_for_rag_index=false`.
  - Measured run results: `20,393` candidates, `490` duplicate text hashes, `87` suspicious-length candidates, `299` preamble warnings.
  - Recommendation: proceed only to Phase 2G filtering rules. Phase 3 remains blocked.
- Phase 2G implementation: **COMPLETE - PASS WITH RISKS**
  - Deterministic review-labeling layer created for Phase 2F candidates.
  - No candidate is approved for RAG or marked as legal ground truth.
  - Measured run results: `20,393` inputs, `511` rejected, `3,249` needs review, `16,633` keep candidates, `339` duplicate hash groups, `490` duplicate candidates rejected, `87` suspicious-length candidates.
  - Parent document warnings are preserved as metadata only and do not automatically force `needs_review`.
  - Phase 3 remains blocked.
- Phase 2H implementation: **COMPLETE - PASS WITH RISKS**
  - Deterministic manual-review sampling pack created from the existing Phase 2G outputs only.
  - Measured run results: `150` sampled rows, `128` parent documents covered, full bucket coverage with no shortfall, `approved_for_rag_index_true_count = 0`, `is_legal_ground_truth_true_count = 0`.
  - Review outputs remain under ignored `artifacts/` only.
  - Human review is still required before any later corpus-candidate gate.
  - Phase 3 remains blocked.
- Phase 2I implementation: **COMPLETE - PASS**
  - Human-review results schema and validator created for the Phase 2H reviewer template.
  - Accepted decision labels and confidence values are now enforced centrally.
  - `legal_ground_truth_approved` and `rag_index_approved` are fail-closed and must remain `false`.
  - Candidate-level adjudication states are defined, but no corpus, RAG, QA, or Phase 3 approval is granted.
  - Phase 3 remains blocked.

