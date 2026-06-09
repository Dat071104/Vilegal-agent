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



