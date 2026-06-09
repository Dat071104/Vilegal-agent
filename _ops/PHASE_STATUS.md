# Phase Status

**Current phase:** Phase 1 - Data Source Audit and Scaffolding  
**Current verdict:** PASS WITH RISKS

## Phase gates

| Phase | Status | Completed |
|---|---|---|
| Phase 0: Project bootstrap structure | PASS | 2026-06-09 |
| Phase 1: Data source audit and scaffolding | PASS WITH RISKS | 2026-06-09 |
| Phase 2: Data pipeline and processing | NOT STARTED - BULK DOWNLOAD BLOCKED | - |
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

