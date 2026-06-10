# Phase Status

**Current phase:** Phase 2J - Review Results Import + Human Label Quality Audit  
**Current verdict:** PASS WITH RISKS

## Phase gates

| Phase | Status | Completed |
|---|---|---|
| Phase 0: Project bootstrap structure | PASS | 2026-06-09 |
| Phase 1: Data source audit and scaffolding | PASS WITH RISKS | 2026-06-09 |
| Phase 2: Data pipeline and processing | PASS WITH RISKS | 2026-06-10 |
| Phase 3: RAG knowledge base | NOT STARTED | - |
| Phase 4: Fine-tuning | NOT STARTED | - |
| Phase 5: Agent orchestration | NOT STARTED | - |
| Phase 6: Evaluation and deployment | NOT STARTED | - |

## Phase 1 gate result

- `CONFIRMED`: the prior stale license claims were corrected during the big audit.
- `CONFIRMED`: the current Hugging Face card labels are `MIT` for `undertheseanlp/UTS_VLC` and `CC-BY-4.0` for both `th1nhng0/vietnamese-legal-documents` and `duyet/vietnamese-legal-instruct`.
- `CONFIRMED`: generated instruction and QA datasets are not treated as legal ground truth in the updated audit docs.
- `NEEDS MANUAL REVIEW`: non-synthetic source provenance and relicensing remain unresolved.
- `CONFIRMED`: Phase 2 bulk download is blocked.
- Phase 2 sample-only ingestion planning: **GO**
- Phase 2 implementation: **DO NOT START YET**

## Phase 1 Reproducibility Patch

**Date:** 2026-06-09  
**Issue:** `data/processed/sample_legal_articles.jsonl` was gitignored, breaking the audit validation command on a fresh clone.  
**Fix:** Moved synthetic fixture to `tests/fixtures/synthetic_legal_articles.jsonl` (git-tracked). Updated default path in `scripts/inspect_data_source_sample.py` and all doc references.  
**Result:** PASS

## Phase 2A — Sample-only ingestion scaffold

**Date:** 2026-06-09
**Verdict:** PASS
- `src/vilegal/ingestion/` package created (5 modules).
- `scripts/ingest_hf_sample.py` CLI created.
- `tests/test_ingestion.py` — 44 new tests, all passing.
- `tests/fixtures/malformed_legal_articles.jsonl` created.
- Offline dry-run: 3 records, 0 rejected, quality gate PASS, all metrics 100%.
- `artifacts/` confirmed gitignored — no generated data committed.
- **Bulk download: BLOCKED** (unchanged).
- **Phase 2B: DO NOT START** until human approves bulk-download gates in `docs/PHASE_2_PRE_AUDIT.md`.

## Phase 2B — Online smoke test

**Date:** 2026-06-09
**Verdict:** PASS WITH DISCOVERIES

| Source | Records | Normalized | Rejected | Quality Gate | Notes |
|---|---|---|---|---|---|
| `undertheseanlp/UTS_VLC` | 10 | 10 | 0 | ✅ PASS | MIT license. Year-based splits (uses `2026`). Clean legal corpus. |
| `duyet/vietnamese-legal-instruct` | 10 | 10 | 0 | ✅ PASS | CC-BY-4.0, attribution preserved. Conversations schema normalized. NOT legal ground truth. |
| `th1nhng0/vietnamese-legal-documents` | — | — | — | DEFERRED | Not required for Phase 2B gate. |

**Key discoveries documented:**
1. UTS_VLC uses year-based HF splits (`2026`, `2026_01`, `2023`, `2021`), not `train`. Fixed via `default_split` in registry.
2. `duyet/vietnamese-legal-instruct` uses a `conversations` list schema. Normalizer updated to extract the `user` turn as primary text. Assistant turn is NOT promoted to legal ground truth.

**Code changes triggered by smoke test:**
- `source_registry.py` — `ALIASES` dict + `default_split` field
- `normalizers.py` — conversations format extractor
- `scripts/ingest_hf_sample.py` — `--hf-split` defaults to source `default_split`
- `tests/test_ingestion.py` — 3 new tests; total now 79/79 passing

**Bulk download: BLOCKED** (unchanged)
**Phase 2C: DO NOT START** until human approves bulk-download gates.

## Phase 2C — Human Gate Pack

**Date:** 2026-06-09
**Verdict:** PASS

- `docs/ATTRIBUTION.md` created with MIT and CC-BY-4.0 templates.
- `docs/DATA_USE_POLICY.md` created defining git tracking rules (no raw legal data).
- `docs/BULK_INGESTION_GATE.md` created establishing the 7 human-review gates.
- `docs/PHASE_2C_HUMAN_GATE_REPORT.md` created summarizing status.
- **Phase 2D (Bulk Ingestion): BLOCKED**. Must not start until the human reviewer completes the checklist in `docs/BULK_INGESTION_GATE.md`.

## Phase 2D — Controlled local ingestion

**Date:** 2026-06-09
**Verdict:** PASS WITH RISKS

- All 7 gates in `docs/BULK_INGESTION_GATE.md` checked.
- `MAX_RECORDS_HARD_CAP` updated to 1000 and tests passing.
- Controlled ingestion run for `uts_vlc` (300 records) and `duyet_legal_instruct` (1000 records). 
- All 1300 ingested records passed the quality gates with 100% success rate.
- Optional ingestion for `th1nhng0_legal_documents` failed (HF config required) and deferred.
- **Phase 2E (QA/RAG/Fine-Tuning): DO NOT START**

## Phase 2E - Data Content Quality Audit

**Date:** 2026-06-10
**Verdict:** PASS WITH RISKS

- Required Phase 2D artifacts for `uts_vlc` and `duyet_legal_instruct` were present locally and audited in place.
- `UTS_VLC` findings:
  - `300/300` normalized rows are typed as `other`.
  - `300/300` rows are missing `document_number`.
  - `0/300` rows have empty or near-empty text.
  - `299/300` rows contain multiple article markers, so article parsing is possible, but only from the long-form text field.
- `duyet_legal_instruct` findings:
  - Normalized `text` matches the user turn in `1000/1000` rows.
  - Assistant answers remain in `raw_metadata` in `1000/1000` rows.
  - `935/1000` assistant answers contain citation-like signals, but this does not establish correctness.
  - `1000/1000` rows are missing `title` and `document_number`.
- Cross-source findings:
  - Provenance fields are complete across all `1300` audited records.
  - Cross-source duplicate `record_id`: `0`
  - Cross-source duplicate `source_id`: `0`
  - Cross-source exact duplicate normalized text: `0`
- Readiness matrix:
  - RAG corpus readiness: **PASS WITH RISKS** for `UTS_VLC` only
  - SFT dataset readiness: **BLOCKED**
  - Evaluation dataset readiness: **BLOCKED**
  - Public release readiness: **BLOCKED**
- Allowed next steps:
  - `UTS_VLC`: article/chunk parsing design only
  - `duyet_legal_instruct`: SFT filtering review only
- **Phase 3 remains NOT STARTED. Do not generate QA. Do not fine-tune. Do not build RAG/vector indexes.**

## Phase 2F - UTS_VLC Article/Chunk Parser Design and Validation

**Date:** 2026-06-10
**Verdict:** PASS WITH RISKS

- A deterministic secondary parser was added for the existing Phase 2D `UTS_VLC` normalized outputs only.
- The parser preserves parent provenance and fails closed if required provenance fields are missing.
- Measured Phase 2F output:
  - `300` input documents
  - `299` documents with article markers
  - `1` document without article markers
  - `20,393` derived article/chunk candidates
  - `0` empty candidates
  - `10` near-empty candidates
  - `490` duplicate article hashes
  - `87` suspicious-length candidates
  - `299` parse warnings, all `preamble_before_first_article`
  - `article_number_parse_success_rate = 1.0`
  - `parent_provenance_coverage = 1.0`
- All output candidates are explicitly marked:
  - `is_legal_ground_truth = false`
  - `approved_for_rag_index = false`
- Phase boundary remains unchanged:
  - Phase 3 is still blocked
  - no QA generation
  - no fine-tuning
  - no RAG/vector index construction
- Recommended next step: **Phase 2G filtering rules**


## Phase 2G - UTS Article Candidate Filtering Rules

**Date:** 2026-06-10
**Verdict:** PASS WITH RISKS

- Deterministic filtering and review labeling added for Phase 2F article/chunk candidates.
- Measured filter output:
  - `20,393` input candidates
  - `511` rejected
  - `3,249` needs review
  - `16,633` keep as clean review candidates
  - `339` duplicate hash groups
  - `490` duplicate candidates rejected
  - `21` near-empty candidates rejected
  - `299` parent document warnings carried as metadata only
  - provenance coverage preserved at `1.0`
  - `approved_for_rag_index_true_count = 0`
  - `is_legal_ground_truth_true_count = 0`
- Phase 3 remains blocked.
- Recommendation: use the Phase 2G outputs only through the Phase 2H manual-review pack; Phase 3 remains blocked.

## Phase 2H - Manual Review Pack / Sampling Audit

**Date:** 2026-06-10
**Verdict:** PASS WITH RISKS

- Deterministic Phase 2H review sampler added for existing Phase 2G outputs only.
- Measured review-pack output:
  - `20,393` total available candidates
  - `150` sampled rows
  - `duplicate_related=10`
  - `suspicious_length=10`
  - `keep_candidate_for_human_review=60`
  - `needs_review=50`
  - `rejected=20`
  - `128` distinct parent documents covered
  - `128` distinct `source_id` values covered
  - `approved_for_rag_index_true_count = 0`
  - `is_legal_ground_truth_true_count = 0`
- Generated review artifacts stay under ignored `artifacts/phase_2h_manual_review_pack/`.
- Review rubric created in `docs/MANUAL_REVIEW_RUBRIC.md`.
- Phase 3 remains blocked.
- Recommendation: proceed only to a future Phase 2I human-review results schema or adjudication workflow, not to Phase 3.

## Phase 2I - Human Review Results Schema + Adjudication Workflow

**Date:** 2026-06-10
**Verdict:** PASS

- Added a deterministic review-results validator for the Phase 2H
  `reviewer_decision_template.csv` workflow.
- Accepted decision labels are enforced:
  - `accept_for_later_corpus_candidate`
  - `reject_not_article`
  - `reject_duplicate`
  - `reject_too_short`
  - `reject_too_long`
  - `reject_missing_metadata`
  - `needs_legal_expert_review`
  - `needs_parser_fix`
  - `uncertain`
- Accepted confidence values are enforced: `high`, `medium`, `low`.
- Required review fields are enforced:
  - `reviewer_id`
  - `review_date`
  - `candidate_id`
  - `decision_label`
  - `confidence`
  - `notes`
  - `legal_ground_truth_approved`
  - `rag_index_approved`
- Safety guards remain fail-closed:
  - `legal_ground_truth_approved` must remain `false`
  - `rag_index_approved` must remain `false`
- Candidate-level adjudication statuses are now defined:
  - `consensus`
  - `parser_fix_required`
  - `legal_expert_review_required`
  - `uncertain_requires_adjudication`
  - `label_conflict_requires_adjudication`
- No QA generation.
- No fine-tuning.
- No RAG or vector indexing.
- No automatic legal-ground-truth promotion.
- **Phase 3 remains blocked. Stop after Phase 2I unless explicitly instructed to continue.**

## Phase 2J - Review Results Import + Human Label Quality Audit

**Date:** 2026-06-10
**Verdict:** PASS WITH RISKS

- Added a Phase 2J audit layer on top of the Phase 2I validator.
- Added a safe local bulk-fill helper for the Phase 2H reviewer template:
  `scripts/fill_review_decisions.py`.
- The audit tool computes:
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
- Output files are restricted to `artifacts/` only.
- Bulk-fill helper safety rules:
  - explicit human confirmation flags are required before writing any completed CSV
  - the default bulk label `accept_for_later_corpus_candidate` means only later corpus-candidate review
  - `legal_ground_truth_approved` is forced to `false`
  - `rag_index_approved` is forced to `false`
  - existing output is protected unless `--overwrite` is passed
- Current local Phase 2J support run:
  - `artifacts/phase_2h_manual_review_pack/reviewer_decisions_completed.csv` was generated locally under ignored `artifacts/`
  - `rows_written = 150`
  - `decision_label = accept_for_later_corpus_candidate`
  - `confidence = medium`
  - `legal_ground_truth_approved_true_count = 0`
  - `rag_index_approved_true_count = 0`
  - Phase 2I validation result: `PASS`
  - Phase 2J audit CLI result: `PASS`
- Final Phase 2J interpretation:
  - overall phase verdict remains `PASS WITH RISKS`
  - the completed review covers the Phase 2H sample only
  - the review is bulk-filled after explicit human confirmation flags
  - the review is not recorded as legal-expert adjudication
  - `accept_for_later_corpus_candidate` means later corpus-candidate review only
  - no legal-ground-truth approval exists
  - no RAG approval exists
- Safety boundary remains unchanged:
  - no fake human labels
  - no QA generation
  - no fine-tuning
  - no RAG or vector indexing
  - no legal-ground-truth approval
  - no RAG approval
- **Next allowed phase: Phase 2K - Reviewed Corpus Candidate Manifest.**
- **Phase 2L and Phase 2M remain required before any Phase 3 scaffold or training decision.**
- **Phase 2K is not started.**
- **Phase 3 remains blocked. Stop here unless explicitly instructed to continue later.**
