# Phase Status

**Current phase:** Phase 2 - Data Pipeline and Processing  
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
